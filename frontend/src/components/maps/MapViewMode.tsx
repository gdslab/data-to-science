import { AxiosResponse } from 'axios';
import { useEffect } from 'react';

import { useMapContext } from './MapContext';
import { MapLayer } from '../pages/workspace/projects/Project';
import CompareMap from './CompareMap';
import HomeMap from './HomeMap';
import PotreeViewer from './PotreeViewer';
import { useMapLayerContext } from './MapLayersContext';

import api from '../../api';
import { mapApiResponseToLayers } from './utils';
import { useRasterSymbologyContext } from './RasterSymbologyContext';

export default function MapViewMode() {
  const {
    activeDataProduct,
    activeMapTool,
    activeProject,
    mapboxAccessTokenDispatch,
  } = useMapContext();
  const {
    state: { layers },
    dispatch,
  } = useMapLayerContext();
  const symbologyContext = useRasterSymbologyContext();

  useEffect(() => {
    if (!import.meta.env.VITE_MAPBOX_ACCESS_TOKEN) {
      fetch('/config.json')
        .then((response) => response.json())
        .then((config) => {
          mapboxAccessTokenDispatch({
            type: 'set',
            payload: config.mapboxAccessToken,
          });
        })
        .catch((error) => {
          console.error('Failed to load config.json:', error);
        });
    } else {
      mapboxAccessTokenDispatch({
        type: 'set',
        payload: import.meta.env.VITE_MAPBOX_ACCESS_TOKEN,
      });
    }
  }, []);

  // Fetch map layers when a project is activated and
  // remove previous raster symbology settings from previous active project
  useEffect(() => {
    const fetchMapLayers = async (projectId: string) => {
      const mapLayersUrl = `/projects/${projectId}/vector_layers`;
      try {
        const response: AxiosResponse<MapLayer[]> = await api.get(mapLayersUrl);
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
        symbologyContext.dispatch({
          type: 'REMOVE_RASTER',
          rasterId: rasterId,
        });
      }
      // Fetch map layers for selected project
      fetchMapLayers(activeProject.id);
    }
  }, [activeProject]);

  if (activeMapTool === 'compare') {
    return <CompareMap />;
  } else if (
    !activeDataProduct ||
    (activeDataProduct && activeDataProduct.data_type !== 'point_cloud')
  ) {
    return <HomeMap layers={layers} />;
  } else {
    const copcPath = activeDataProduct.url;
    return <PotreeViewer copcPath={copcPath} />;
  }
}
