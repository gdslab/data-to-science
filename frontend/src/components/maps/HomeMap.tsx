import 'maplibre-gl/dist/maplibre-gl.css';
import './HomeMap.css';
import { Feature } from 'geojson';
import maplibregl from 'maplibre-gl';
import { useEffect, useMemo, useState } from 'react';
import Map, { NavigationControl, ScaleControl } from 'react-map-gl/maplibre';
import { useLocation } from 'react-router-dom';
// import { bbox } from '@turf/bbox';

import ColorBarControl from './ColorBarControl';
import GeocoderControl from './GeocoderControl';
import ProjectCluster from './ProjectCluster';
import FeaturePopup from './FeaturePopup';
import LayerControl from './LayerControl';
import ProjectBoundary from './ProjectBoundary';
import ProjectPopup from './ProjectPopup';
import ProjectRasterTiles from './ProjectRasterTiles';
import ProjectVectorTiles from './ProjectVectorTiles';

// import { BBox } from './Maps';
import { useMapContext } from './MapContext';
import { MapLayerProps } from './MapLayersContext';
import {
  SingleBandSymbology,
  useRasterSymbologyContext,
} from './RasterSymbologyContext';

import {
  getMapboxSatelliteBasemapStyle,
  usgsImageryTopoBasemapStyle,
} from './styles/basemapStyles';

import { isSingleBand } from './utils';
import { BBox } from './Maps';

export type PopupInfoProps = {
  feature: Feature;
  feature_type: string;
  latitude: number;
  longitude: number;
};

export default function HomeMap({ layers }: { layers: MapLayerProps[] }) {
  const [activeProjectBBox, setActiveProjectBBox] = useState<BBox | null>(null);
  const [isMapReady, setIsMapReady] = useState(false);
  const [popupInfo, setPopupInfo] = useState<
    PopupInfoProps | { [key: string]: any } | null
  >(null);

  const {
    activeDataProduct,
    activeProject,
    mapboxAccessToken,
    projects,
    projectsVisibleDispatch,
  } = useMapContext();
  const symbologyContext = useRasterSymbologyContext();

  const { state } = useLocation();

  // Set map state to ready if user has zero projects
  useEffect(() => {
    if (projects && projects.length === 0) {
      setIsMapReady(true);
    }
  }, [projects]);

  // Set to ready state if home map was navigated to from a data product card
  useEffect(() => {
    if (state?.navContext === 'dataProductCard') {
      setIsMapReady(true);
    }
  }, [state]);

  // Set map state to ready if a project is activated
  useEffect(() => {
    if (activeProject && !isMapReady) {
      setIsMapReady(true);
    }
  }, [activeProject]);

  const handleMapClick = (event) => {
    const map: maplibregl.Map = event.target;

    if (map.getLayer('unclustered-point')) {
      const features = map.queryRenderedFeatures(event.point, {
        layers: ['unclustered-point'],
      });

      if (features.length > 0) {
        const clickedFeature = features[0];

        if (clickedFeature.geometry.type === 'Point') {
          const coordinates = clickedFeature.geometry.coordinates;

          setPopupInfo({
            feature: clickedFeature,
            feature_type: 'point',
            latitude: coordinates[1],
            longitude: coordinates[0],
          });
        }
      }
    }

    if (layers.length > 0) {
      for (const layer of layers) {
        if (layer.checked && map.getLayer(layer.id)) {
          const features = map.queryRenderedFeatures(event.point, {
            layers: [layer.id],
          });

          if (features.length > 0) {
            const clickedFeature = features[0];
            const clickCoordinates = event.lngLat;
            const clickedFeatureType =
              clickedFeature.geometry.type.toLowerCase();

            setPopupInfo({
              feature: clickedFeature,
              feature_type: clickedFeatureType,
              latitude: clickCoordinates.lat,
              longitude: clickCoordinates.lng,
            });
          }
        }
      }
    }
  };

  const handleMoveEnd = (event) => {
    if (!projects?.length) return;

    const mapInstance = event.target;
    const mapBounds = mapInstance.getBounds();

    // Filter projects to those whose marker is inside the current map bounds,
    // then extract their IDs
    const visibleProjectMarkers = projects
      .filter((project) => {
        const { x, y } = project.centroid;
        const markerLocation = new maplibregl.LngLat(x, y);
        return mapBounds.contains(markerLocation);
      })
      .map((project) => project.id);

    // Update state with visible project marker IDs
    projectsVisibleDispatch({
      type: 'set',
      payload: visibleProjectMarkers,
    });
  };

  const showBackgroundRaster = () => {
    if (
      activeProject &&
      activeDataProduct &&
      isSingleBand(activeDataProduct) &&
      symbologyContext.state[activeDataProduct.id]
    ) {
      const activeDataProductSymbology = symbologyContext.state[
        activeDataProduct.id
      ].symbology as SingleBandSymbology;
      if (activeDataProductSymbology && activeDataProductSymbology.background) {
        const boundingBox =
          activeDataProduct.bbox || activeProjectBBox || undefined;
        return (
          <ProjectRasterTiles
            boundingBox={boundingBox}
            dataProduct={activeDataProductSymbology.background}
          />
        );
      } else {
        return null;
      }
    } else {
      return null;
    }
  };

  const mapStyle = useMemo(() => {
    return mapboxAccessToken
      ? getMapboxSatelliteBasemapStyle(mapboxAccessToken)
      : usgsImageryTopoBasemapStyle;
  }, [mapboxAccessToken]);

  return (
    <Map
      initialViewState={{
        longitude: -86.9138040788386,
        latitude: 40.428655143949925,
      }}
      style={{
        width: '100%',
        height: '100%',
        opacity: isMapReady ? 1 : 0,
      }}
      mapboxAccessToken={mapboxAccessToken || undefined}
      mapStyle={mapStyle}
      onClick={handleMapClick}
      onMoveEnd={handleMoveEnd}
    >
      {/* Display marker cluster for project centroids when no project is active */}
      {!activeProject && (
        <ProjectCluster isMapReady={isMapReady} setIsMapReady={setIsMapReady} />
      )}

      {/* Display popup on click for project markers when no project is active */}
      {!activeProject && popupInfo && (
        <ProjectPopup
          popupInfo={popupInfo}
          onClose={() => setPopupInfo(null)}
        />
      )}

      {/* Display popup on click on map layer feature */}
      {activeProject && popupInfo && (
        <FeaturePopup
          popupInfo={popupInfo}
          onClose={() => setPopupInfo(null)}
        />
      )}

      {/* Display project raster tiles when project active and data product active */}
      {activeProject && activeDataProduct && (
        <ProjectRasterTiles
          key={activeDataProduct.id}
          boundingBox={activeDataProduct.bbox || activeProjectBBox || undefined}
          dataProduct={activeDataProduct}
        />
      )}
      {/* Show background raster if one is set */}
      {activeProject && activeDataProduct && showBackgroundRaster()}

      {/* Display color bar when project active and single band data product active */}
      {activeProject &&
        activeDataProduct &&
        isSingleBand(activeDataProduct) && (
          <ColorBarControl
            dataProduct={activeDataProduct}
            projectId={activeProject.id}
          />
        )}

      {/* Display project vector layers when project active and layers selected */}
      {activeProject && <ProjectVectorTiles />}

      {/* Display project boundary when project activated */}
      {activeProject && (
        <ProjectBoundary setActiveProjectBBox={setActiveProjectBBox} />
      )}

      {/* Project map layer controls */}
      {activeProject && <LayerControl />}

      {/* General controls */}
      {!activeProject && <GeocoderControl />}
      <NavigationControl />
      <ScaleControl />
    </Map>
  );
}
