import 'maplibre-gl/dist/maplibre-gl.css';
import './HomeMap.css';
import axios, { AxiosResponse } from 'axios';
import { Feature } from 'geojson';
import { useEffect, useState } from 'react';
import Map, { NavigationControl, ScaleControl } from 'react-map-gl/maplibre';

import ColorBarControl from './ColorBarControl';
import GeocoderControl from './GeocoderControl';
import ProjectCluster from './ProjectCluster';
import FeaturePopup from './FeaturePopup';
import LayerControl from './LayerControl';
import ProjectBoundary from './ProjectBoundary';
import ProjectPopup from './ProjectPopup';
import ProjectRasterTiles from './ProjectRasterTiles';
import ProjectVectorTiles from './ProjectVectorTiles';
import { MapLayer } from '../pages/projects/Project';

import { useMapContext } from './MapContext';
import { useMapLayerContext } from './MapLayersContext';
import { useRasterSymbologyContext } from './RasterSymbologyContext';

import {
  mapboxSatelliteBasemapStyle,
  usgsImageryTopoBasemapStyle,
} from './styles/basemapStyles';

import { isSingleBand, mapApiResponseToLayers } from './utils';

export type PopupInfoProps = {
  feature: Feature;
  latitude: number;
  longitude: number;
};

export default function HomeMap() {
  const [popupInfo, setPopupInfo] = useState<
    PopupInfoProps | { [key: string]: any } | null
  >(null);
  const { activeDataProduct, activeProject } = useMapContext();
  const {
    state: { layers },
    dispatch,
  } = useMapLayerContext();
  const symbologyContext = useRasterSymbologyContext();

  // Fetch map layers when a project is activated
  useEffect(() => {
    const fetchMapLayers = async (projectId: string) => {
      const mapLayersUrl = `${
        import.meta.env.VITE_API_V1_STR
      }/projects/${projectId}/vector_layers`;
      try {
        const response: AxiosResponse<MapLayer[]> = await axios.get(mapLayersUrl);
        dispatch({
          type: 'SET_LAYERS',
          payload: mapApiResponseToLayers(response.data),
        });
      } catch (error) {
        console.error('Error fetching project map layers:', error);
        dispatch({ type: 'SET_LAYERS', payload: [] });
      }
    };
    if (activeProject) {
      // Remove any symbology settings for rasters from previously selected project
      for (const rasterId in symbologyContext.state) {
        symbologyContext.dispatch({ type: 'REMOVE_RASTER', rasterId: rasterId });
      }
      // Fetch map layers for selected project
      fetchMapLayers(activeProject.id);
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

            setPopupInfo({
              feature: clickedFeature,
              latitude: clickCoordinates.lat,
              longitude: clickCoordinates.lng,
            });
          }
        }
      }
    }
  };

  return (
    <Map
      initialViewState={{
        longitude: -86.9138040788386,
        latitude: 40.428655143949925,
        zoom: 8,
      }}
      style={{
        width: '100%',
        height: '100%',
      }}
      mapboxAccessToken={import.meta.env.VITE_MAPBOX_ACCESS_TOKEN || undefined}
      mapStyle={
        import.meta.env.VITE_MAPBOX_ACCESS_TOKEN
          ? mapboxSatelliteBasemapStyle
          : usgsImageryTopoBasemapStyle
      }
      reuseMaps={true}
      onClick={handleMapClick}
    >
      {/* Display marker cluster for project centroids when no project is active */}
      {!activeProject && <ProjectCluster />}

      {/* Display popup on click for project markers when no project is active */}
      {!activeProject && popupInfo && (
        <ProjectPopup popupInfo={popupInfo} onClose={() => setPopupInfo(null)} />
      )}

      {/* Display popup on click on map layer feature */}
      {activeProject && popupInfo && (
        <FeaturePopup popupInfo={popupInfo} onClose={() => setPopupInfo(null)} />
      )}

      {/* Display project raster tiles when project active and data product active */}
      {activeProject && activeDataProduct && (
        <ProjectRasterTiles
          key={activeDataProduct.id}
          dataProduct={activeDataProduct}
        />
      )}

      {/* Display color bar when project active and single band data product active */}
      {activeProject && activeDataProduct && isSingleBand(activeDataProduct) && (
        <ColorBarControl dataProduct={activeDataProduct} projectId={activeProject.id} />
      )}

      {/* Display project vector layers when project active and layers selected */}
      {activeProject && <ProjectVectorTiles />}

      {/* Display project boundary when project activated */}
      {activeProject && <ProjectBoundary />}

      {/* Project map layer controls */}
      {activeProject && <LayerControl />}

      {/* General controls */}
      {!activeProject && <GeocoderControl />}
      <NavigationControl />
      <ScaleControl />
    </Map>
  );
}
