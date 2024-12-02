import 'maplibre-gl/dist/maplibre-gl.css';
import './MaplibreMap.css';
import axios, { AxiosResponse } from 'axios';
import { StyleSpecification } from 'maplibre-gl';
import { useEffect, useState } from 'react';
import Map, {
  GeolocateControl,
  NavigationControl,
  Popup,
  ScaleControl,
} from 'react-map-gl/maplibre';

import { useMapContext } from './MapContext';
import MaplibreCluster from './MaplibreCluster';
import MaplibreProjectBoundary from './MaplibreProjectBoundary';
import MaplibreProjectVectorTiles from './MaplibreProjectVectorTiles';
import MaplibreProjectRasterTiles from './MaplibreProjectRasterTiles';
import MaplibreLayerControl from './MaplibreLayerControl';
import { useMapLayerContext } from './MapLayersContext';
import { MapLayer } from '../pages/projects/Project';

import { mapApiResponseToLayers } from './utils';

type ProjectPopup = {
  id: string;
  title: string;
  description: string;
  latitude: number;
  longitude: number;
};

const satelliteBasemapStyle: StyleSpecification = {
  version: 8,
  glyphs: `https://api.maptiler.com/fonts/{fontstack}/{range}.pbf?key=${
    import.meta.env.VITE_MAPTILER_API_KEY
  }`,
  sources: {
    satellite: {
      type: 'raster',
      tiles: [
        `https://api.mapbox.com/styles/v1/mapbox/satellite-streets-v12/tiles/{z}/{x}/{y}?access_token=${
          import.meta.env.VITE_MAPBOX_ACCESS_TOKEN
        }`,
      ],
      tileSize: 256,
    },
  },
  layers: [
    {
      id: 'satellite-layer',
      type: 'raster',
      source: 'satellite',
    },
  ],
};

export default function MaplibreMap() {
  const [popupInfo, setPopupInfo] = useState<
    ProjectPopup | { [key: string]: any } | null
  >(null);
  const {
    activeDataProduct,
    activeMapTool,
    activeProject,
    activeProjectDispatch,
    projects,
  } = useMapContext();
  const {
    state: { layers },
    dispatch,
  } = useMapLayerContext();

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
        const coordinates = clickedFeature.geometry.coordinates;
        const properties = features[0].properties as ProjectPopup;

        setPopupInfo({
          ...properties,
          latitude: coordinates[1],
          longitude: coordinates[0],
        });
      }
    }

    if (layers.length > 0) {
      for (const layer of layers) {
        if (layer.checked && map.getLayer(layer.id)) {
          const features = map.queryRenderedFeatures(event.point, {
            layers: [layer.id],
          });

          if (features.length > 0) {
            const clickCoordinates = event.lngLat;
            const properties = features[0].properties as { [key: string]: any };

            setPopupInfo({
              ...properties,
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
      mapboxAccessToken={import.meta.env.VITE_MAPBOX_ACCESS_TOKEN}
      mapStyle={satelliteBasemapStyle}
      reuseMaps={true}
      onClick={handleMapClick}
    >
      {/* Display marker cluster for project centroids when no project is active */}
      {activeMapTool === 'map' && !activeProject && <MaplibreCluster />}

      {/* Display popup on click for project markers when no project is active */}
      {activeMapTool === 'map' && !activeProject && popupInfo && (
        <Popup
          anchor="top"
          longitude={popupInfo.longitude}
          latitude={popupInfo.latitude}
          onClose={() => setPopupInfo(null)}
          style={{ width: '240px' }}
        >
          <article className="flex flex-col gap-2 text-wrap">
            <h3>{popupInfo.title}</h3>
            <p>{popupInfo.description}</p>
            <button
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-300"
              onClick={() => {
                const thisProject = projects?.filter(({ id }) => id === popupInfo.id);
                if (thisProject && thisProject.length === 1) {
                  activeProjectDispatch({ type: 'set', payload: thisProject[0] });
                  setPopupInfo(null);
                }
              }}
            >
              Open
            </button>
          </article>
        </Popup>
      )}

      {/* Display popup on click on map layer feature */}
      {activeMapTool === 'map' && activeProject && popupInfo && (
        <Popup
          anchor="top"
          longitude={popupInfo.longitude}
          latitude={popupInfo.latitude}
          onClose={() => setPopupInfo(null)}
          style={{ width: '240px' }}
        >
          <article className="flex flex-col gap-2 text-wrap">
            <pre>{JSON.stringify(popupInfo, null, 2)}</pre>
          </article>
        </Popup>
      )}

      {/* Display project raster tiles when project active and data product active */}
      {activeMapTool === 'map' && activeProject && activeDataProduct && (
        <MaplibreProjectRasterTiles
          key={activeDataProduct.id}
          dataProduct={activeDataProduct}
        />
      )}

      {/* Display project vector layers when project active and layers selected */}
      {activeMapTool === 'map' && activeProject && <MaplibreProjectVectorTiles />}

      {/* Display project boundary when project activated */}
      {activeMapTool === 'map' && activeProject && <MaplibreProjectBoundary />}

      {/* Project map layer controls */}
      {activeMapTool === 'map' && activeProject && <MaplibreLayerControl />}

      {/* General controls */}
      <GeolocateControl />
      <NavigationControl />
      <ScaleControl />
    </Map>
  );
}
