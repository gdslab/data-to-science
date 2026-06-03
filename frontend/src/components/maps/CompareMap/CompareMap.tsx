import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import Map, { MapRef, MapMouseEvent, ScaleControl } from 'react-map-gl/maplibre';
import squareGrid from '@turf/square-grid';
import distance from '@turf/distance';
import { point } from '@turf/helpers';
import { FeatureCollection, Polygon } from 'geojson';

import ColorBarControl from '../ColorBarControl';
import CompareMapControl from './CompareMapControl';
import CompareToolsControl from './CompareToolsControl';
import GridOverlay from './GridOverlay';
import PointSyncMarkers from './PointSyncMarkers';
import SwipeSlider from './SwipeSlider';
import CompareModeControl, { Mode } from './CompareModeControl';
import ProjectBoundary from '../ProjectBoundary';
import { useMapContext } from '../MapContext';
import { useMapApiKeys } from '../MapApiKeysContext';
import ProjectRasterTiles from '../ProjectRasterTiles';
import { useRasterSymbologyContext } from '../RasterSymbologyContext';

import { BBox } from '../Maps';
import {
  getMapboxSatelliteBasemapStyle,
  getWorldImageryTopoBasemapStyle,
} from '../styles/basemapStyles';
import {
  createDefaultMultibandSymbology,
  createDefaultSingleBandSymbology,
} from '../utils';
import { isSingleBand } from '../utils';

type SyncPoint = {
  lng: number;
  lat: number;
  originSide: 'left' | 'right';
};

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
  // State
  const [viewState, setViewState] = useState({
    longitude: -86.9138040788386,
    latitude: 40.428655143949925,
    zoom: 8,
  });
  const [sliderPosition, setSliderPosition] = useState(50); // Percentage
  const [mode, setMode] = useState<Mode>('split-screen');
  const [activeMap, setActiveMap] = useState<'left' | 'right'>('left');
  const [mapComparisonState, setMapComparisonState] =
    useState<MapComparisonState>(defaultMapComparisonState);
  const [activeProjectBBox, setActiveProjectBBox] = useState<BBox | null>(null);
  const [showGrid, setShowGrid] = useState(false);
  const [pointSyncActive, setPointSyncActive] = useState(false);
  const [syncPoint, setSyncPoint] = useState<SyncPoint | null>(null);

  // Refs
  const leftMapRef = useRef<MapRef>(null);
  const rightMapRef = useRef<MapRef>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Context
  const { activeProject, flights } = useMapContext();
  const { mapboxAccessToken, maptilerApiKey } = useMapApiKeys();
  const { state: symbologyState, dispatch } = useRasterSymbologyContext();

  // Event handlers
  const onLeftMoveStart = useCallback(() => setActiveMap('left'), []);
  const onRightMoveStart = useCallback(() => setActiveMap('right'), []);
  const onMove = useCallback((evt) => setViewState(evt.viewState), []);

  const onLeftClick = useCallback(
    (evt: MapMouseEvent) => {
      if (!pointSyncActive) return;
      setSyncPoint({ lng: evt.lngLat.lng, lat: evt.lngLat.lat, originSide: 'left' });
    },
    [pointSyncActive]
  );

  const onRightClick = useCallback(
    (evt: MapMouseEvent) => {
      if (!pointSyncActive) return;
      setSyncPoint({ lng: evt.lngLat.lng, lat: evt.lngLat.lat, originSide: 'right' });
    },
    [pointSyncActive]
  );

  const handleTogglePointSync = useCallback(() => {
    setPointSyncActive((prev) => {
      if (prev) setSyncPoint(null);
      return !prev;
    });
  }, []);

  // Compute square grid from project bounding box (~10 cells across the larger dimension)
  const compareGrid = useMemo((): FeatureCollection<Polygon> | null => {
    if (!activeProjectBBox) return null;
    const [minLng, minLat, maxLng, maxLat] = activeProjectBBox;
    const widthKm = distance(point([minLng, minLat]), point([maxLng, minLat]), {
      units: 'kilometers',
    });
    const heightKm = distance(point([minLng, minLat]), point([minLng, maxLat]), {
      units: 'kilometers',
    });
    const cellSide = Math.max(widthKm, heightKm) / 10;
    if (cellSide <= 0) return null;
    return squareGrid(activeProjectBBox, cellSide, { units: 'kilometers' });
  }, [activeProjectBBox]);

  // Selected data products
  const selectedLeftDataProduct = useMemo(
    () =>
      flights
        .find(({ id }) => id === mapComparisonState.left?.flightId)
        ?.data_products.find(
          ({ id }) => id === mapComparisonState.left?.dataProductId
        ) || null,
    [flights, mapComparisonState.left]
  );

  const selectedRightDataProduct = useMemo(
    () =>
      flights
        .find(({ id }) => id === mapComparisonState.right?.flightId)
        ?.data_products.find(
          ({ id }) => id === mapComparisonState.right?.dataProductId
        ) || null,
    [flights, mapComparisonState.right]
  );

  // Symbology initialization for left data product
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
  }, [dispatch, selectedLeftDataProduct]);

  // Symbology initialization for right data product
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
  }, [dispatch, selectedRightDataProduct]);

  const mapStyle = useMemo(() => {
    return mapboxAccessToken
      ? getMapboxSatelliteBasemapStyle(mapboxAccessToken)
      : getWorldImageryTopoBasemapStyle(maptilerApiKey);
  }, [mapboxAccessToken, maptilerApiKey]);

  // Force map resize after initial render to fix dimension calculation issues
  useEffect(() => {
    const timer = setTimeout(() => {
      leftMapRef.current?.resize();
      rightMapRef.current?.resize();
    }, 100);

    return () => clearTimeout(timer);
  }, []);

  // Resize maps when mode changes
  useEffect(() => {
    const timer = setTimeout(() => {
      leftMapRef.current?.resize();
      rightMapRef.current?.resize();
    }, 100);

    return () => clearTimeout(timer);
  }, [mode]);

  // Styles with conditional rendering based on mode
  const leftMapStyle: React.CSSProperties = useMemo(
    () => ({
      position: 'absolute',
      width: mode === 'side-by-side' ? '50%' : '100%',
      height: '100%',
      clipPath:
        mode === 'split-screen'
          ? `inset(0 ${100 - sliderPosition}% 0 0)`
          : 'none',
      borderRight: mode === 'side-by-side' ? '2px solid white' : 'none',
    }),
    [sliderPosition, mode]
  );

  const rightMapStyle: React.CSSProperties = useMemo(
    () => ({
      position: 'absolute',
      left: mode === 'side-by-side' ? '50%' : 0,
      width: mode === 'side-by-side' ? '50%' : '100%',
      height: '100%',
      clipPath:
        mode === 'split-screen' ? `inset(0 0 0 ${sliderPosition}%)` : 'none',
    }),
    [sliderPosition, mode]
  );

  return (
    <div ref={containerRef} className="relative h-full overflow-x-hidden">
      {/* Left Map - clipped from right */}
      <Map
        ref={leftMapRef}
        {...viewState}
        onMoveStart={onLeftMoveStart}
        onMove={activeMap === 'left' ? onMove : undefined}
        onClick={onLeftClick}
        cursor={pointSyncActive ? 'crosshair' : undefined}
        style={leftMapStyle}
        mapboxAccessToken={mapboxAccessToken || undefined}
        mapStyle={mapStyle}
        maxZoom={25}
        reuseMaps={true}
      >
        {/* Display project boundary when project activated */}
        {activeProject && (
          <ProjectBoundary setActiveProjectBBox={setActiveProjectBBox} />
        )}

        {activeProject &&
          selectedLeftDataProduct &&
          symbologyState[selectedLeftDataProduct.id]?.isLoaded && (
            <ProjectRasterTiles
              boundingBox={
                selectedLeftDataProduct.bbox || activeProjectBBox || undefined
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

        {/* Grid overlay */}
        {activeProject && showGrid && compareGrid && (
          <GridOverlay data={compareGrid} side="left" />
        )}

        {/* Point sync marker */}
        {pointSyncActive && syncPoint && (
          <PointSyncMarkers syncPoint={syncPoint} side="left" />
        )}

        <ScaleControl />
      </Map>

      {/* Right Map - clipped from left */}
      <Map
        ref={rightMapRef}
        {...viewState}
        onMoveStart={onRightMoveStart}
        onMove={activeMap === 'right' ? onMove : undefined}
        onClick={onRightClick}
        cursor={pointSyncActive ? 'crosshair' : undefined}
        style={rightMapStyle}
        mapboxAccessToken={mapboxAccessToken}
        mapStyle={mapStyle}
        maxZoom={25}
        reuseMaps={true}
      >
        {/* Display project boundary when project activated */}
        {activeProject && <ProjectBoundary />}

        {activeProject &&
          selectedRightDataProduct &&
          symbologyState[selectedRightDataProduct.id]?.isLoaded && (
            <ProjectRasterTiles
              boundingBox={
                selectedRightDataProduct.bbox || activeProjectBBox || undefined
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

        {/* Grid overlay */}
        {activeProject && showGrid && compareGrid && (
          <GridOverlay data={compareGrid} side="right" />
        )}

        {/* Point sync marker */}
        {pointSyncActive && syncPoint && (
          <PointSyncMarkers syncPoint={syncPoint} side="right" />
        )}

        <ScaleControl />
      </Map>

      {/* Draggable Swipe Slider - only in split-screen mode */}
      {mode === 'split-screen' && (
        <SwipeSlider
          position={sliderPosition}
          onPositionChange={setSliderPosition}
          containerRef={containerRef}
        />
      )}

      {/* Bottom controls row: tool toggles (left) + mode selector (right) */}
      <div
        className="absolute bottom-12 left-1/2 -translate-x-1/2 flex flex-col items-center gap-1"
        style={{ zIndex: 1001 }}
      >
        <CompareToolsControl
          showGrid={showGrid}
          onToggleGrid={() => setShowGrid((prev) => !prev)}
          pointSyncActive={pointSyncActive}
          onTogglePointSync={handleTogglePointSync}
        />
        <CompareModeControl mode={mode} onModeChange={setMode} />
      </div>

      {/* Data product selection controls (outside maps so they're never clipped) */}
      <CompareMapControl
        flights={flights}
        mapComparisonState={mapComparisonState}
        setMapComparisonState={setMapComparisonState}
        side="left"
      />

      <CompareMapControl
        flights={flights}
        mapComparisonState={mapComparisonState}
        setMapComparisonState={setMapComparisonState}
        side="right"
      />
    </div>
  );
}
