import { useCallback, useEffect, useMemo, useState } from 'react';
import Map, { NavigationControl, ScaleControl } from 'react-map-gl/maplibre';
import { bbox } from '@turf/bbox';

import ColorBarControl from '../ColorBarControl';
import CompareMapControl from './CompareMapControl';
import CompareModeControl from './CompareModeControl';
import ProjectBoundary from '../ProjectBoundary';
import { useMapContext } from '../MapContext';
import ProjectRasterTiles from '../ProjectRasterTiles';
import { DataProduct } from '../../pages/workspace/projects/Project';
import { useRasterSymbologyContext } from '../RasterSymbologyContext';

import { BBox } from '../Maps';
import {
  getMapboxSatelliteBasemapStyle,
  usgsImageryTopoBasemapStyle,
} from '../styles/basemapStyles';
import {
  createDefaultMultibandSymbology,
  createDefaultSingleBandSymbology,
} from '../utils';
import { isSingleBand } from '../utils';

const LeftMapStyle: React.CSSProperties = {
  position: 'absolute',
  width: '50%',
  height: '100%',
  borderRightWidth: 2,
  borderRightColor: 'white',
};
const RightMapStyle: React.CSSProperties = {
  position: 'absolute',
  left: '50%',
  width: '50%',
  height: '100%',
};

type Mode = 'split-screen' | 'side-by-side';

export type MapComparisonState = {
  left: {
    flightId: string | undefined;
    dataProductId: string | undefined;
  };
  right: {
    flightId: string | undefined;
    dataProductId: string | undefined;
  };
};

const defaultMapComparisonState = {
  left: {
    flightId: undefined,
    dataProductId: undefined,
  },
  right: {
    flightId: undefined,
    dataProductId: undefined,
  },
};

export default function CompareMap() {
  const [viewState, setViewState] = useState({
    longitude: -86.9138040788386,
    latitude: 40.428655143949925,
    zoom: 8,
  });
  const [mode, setMode] = useState<Mode>('split-screen');

  const [activeMap, setActiveMap] = useState<'left' | 'right'>('left');

  const [mapComparisonState, setMapComparisonState] =
    useState<MapComparisonState>(defaultMapComparisonState);

  const { activeProject, flights, mapboxAccessToken } = useMapContext();

  const { state: symbologyState, dispatch } = useRasterSymbologyContext();

  const onLeftMoveStart = useCallback(() => setActiveMap('left'), []);
  const onRightMoveStart = useCallback(() => setActiveMap('right'), []);
  const onMove = useCallback((evt) => setViewState(evt.viewState), []);

  const width = typeof window === 'undefined' ? 100 : window.innerWidth;
  const leftMapPadding = useMemo(() => {
    return {
      left: mode === 'split-screen' ? width / 2 : 0,
      top: 0,
      right: 0,
      bottom: 0,
    };
  }, [width, mode]);
  const rightMapPadding = useMemo(() => {
    return {
      right: mode === 'split-screen' ? width / 2 : 0,
      top: 0,
      left: 0,
      bottom: 0,
    };
  }, [width, mode]);

  const getDataProduct = (side: 'left' | 'right'): DataProduct | null => {
    return (
      flights
        .find(({ id }) => id === mapComparisonState[side]?.flightId)
        ?.data_products.find(
          ({ id }) => id === mapComparisonState[side]?.dataProductId
        ) || null
    );
  };

  const selectedLeftDataProduct = useMemo(
    () => getDataProduct('left'),
    [flights, mapComparisonState.left]
  );

  const selectedRightDataProduct = useMemo(
    () => getDataProduct('right'),
    [flights, mapComparisonState.right]
  );

  useEffect(() => {
    if (selectedLeftDataProduct) {
      const { id, stac_properties, user_style } = selectedLeftDataProduct;

      if (user_style) {
        // default opacity to 100 for older saved styles that are missing this property
        dispatch({
          type: 'SET_SYMBOLOGY',
          rasterId: id,
          payload: { ...user_style, opacity: user_style.opacity ?? 100 },
        });
      } else if (isSingleBand(selectedLeftDataProduct)) {
        dispatch({
          type: 'SET_SYMBOLOGY',
          rasterId: id,
          payload: createDefaultSingleBandSymbology(stac_properties),
        });
      } else {
        dispatch({
          type: 'SET_SYMBOLOGY',
          rasterId: id,
          payload: createDefaultMultibandSymbology(stac_properties),
        });
      }

      // update ready state for symbology
      dispatch({
        type: 'SET_READY_STATE',
        rasterId: id,
        payload: true,
      });
    }
  }, [selectedLeftDataProduct]);

  useEffect(() => {
    if (selectedRightDataProduct) {
      const { id, stac_properties, user_style } = selectedRightDataProduct;
      if (user_style) {
        // default opacity to 100 for older saved styles that are missing this property
        dispatch({
          type: 'SET_SYMBOLOGY',
          rasterId: id,
          payload: { ...user_style, opacity: user_style.opacity ?? 100 },
        });
      } else if (isSingleBand(selectedRightDataProduct)) {
        dispatch({
          type: 'SET_SYMBOLOGY',
          rasterId: id,
          payload: createDefaultSingleBandSymbology(stac_properties),
        });
      } else {
        dispatch({
          type: 'SET_SYMBOLOGY',
          rasterId: id,
          payload: createDefaultMultibandSymbology(stac_properties),
        });
      }

      // update ready state for symbology
      dispatch({
        type: 'SET_READY_STATE',
        rasterId: id,
        payload: true,
      });
    }
  }, [selectedRightDataProduct]);

  const mapStyle = useMemo(() => {
    return mapboxAccessToken
      ? getMapboxSatelliteBasemapStyle(mapboxAccessToken)
      : usgsImageryTopoBasemapStyle;
  }, [mapboxAccessToken]);

  return (
    <div className="relative h-full">
      <Map
        {...viewState}
        padding={leftMapPadding}
        onMoveStart={onLeftMoveStart}
        onMove={activeMap === 'left' ? onMove : undefined}
        style={LeftMapStyle}
        mapboxAccessToken={mapboxAccessToken || undefined}
        mapStyle={mapStyle}
        reuseMaps={true}
      >
        {/* Display project boundary when project activated */}
        {activeProject && <ProjectBoundary setViewState={setViewState} />}

        <CompareMapControl
          flights={flights}
          mapComparisonState={mapComparisonState}
          setMapComparisonState={setMapComparisonState}
          side="left"
        />

        {activeProject &&
          selectedLeftDataProduct &&
          symbologyState[selectedLeftDataProduct.id]?.isLoaded && (
            <ProjectRasterTiles
              boundingBox={
                selectedLeftDataProduct.bbox ||
                (bbox(activeProject.field) as BBox)
              }
              dataProduct={selectedLeftDataProduct}
            />
          )}

        {/* Display color bar when project active and single band data product active */}
        {activeProject &&
          selectedLeftDataProduct &&
          isSingleBand(selectedLeftDataProduct) && (
            <ColorBarControl
              dataProduct={selectedLeftDataProduct}
              projectId={activeProject.id}
            />
          )}

        {/* Toggle compare mode */}
        <CompareModeControl mode={mode} onModeChange={setMode} />

        {/* General controls */}
        <NavigationControl position="top-left" />
        <ScaleControl />
      </Map>
      <Map
        {...viewState}
        padding={rightMapPadding}
        onMoveStart={onRightMoveStart}
        onMove={activeMap === 'right' ? onMove : undefined}
        style={RightMapStyle}
        mapboxAccessToken={mapboxAccessToken}
        mapStyle={mapStyle}
        reuseMaps={true}
      >
        {/* Display project boundary when project activated */}
        {activeProject && <ProjectBoundary />}

        <CompareMapControl
          flights={flights}
          mapComparisonState={mapComparisonState}
          setMapComparisonState={setMapComparisonState}
          side="right"
        />

        {activeProject &&
          selectedRightDataProduct &&
          symbologyState[selectedRightDataProduct.id]?.isLoaded && (
            <ProjectRasterTiles
              boundingBox={
                selectedRightDataProduct.bbox ||
                (bbox(activeProject.field) as BBox)
              }
              dataProduct={selectedRightDataProduct}
            />
          )}

        {/* Display color bar when project active and single band data product active */}
        {activeProject &&
          selectedRightDataProduct &&
          isSingleBand(selectedRightDataProduct) && (
            <ColorBarControl
              dataProduct={selectedRightDataProduct}
              position="right"
              projectId={activeProject.id}
            />
          )}

        {/* General controls */}
        <NavigationControl />
        <ScaleControl />
      </Map>
    </div>
  );
}
