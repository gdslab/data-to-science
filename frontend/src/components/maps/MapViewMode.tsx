import { AxiosResponse } from 'axios';
import { useEffect } from 'react';

import { useMapContext } from './MapContext';
import { useMapApiKeys } from './MapApiKeysContext';
import { MapLayer } from '../pages/projects/Project';
import CompareMap from './CompareMap';
import HomeMap from './HomeMap';
import PanoViewer from './PanoViewer';
import PotreeViewer from './PotreeViewer';
import ThreeDGSViewer from './ThreeDGSViewer';
import { useMapLayerContext } from './MapLayersContext';

import api from '../../api';
import { mapApiResponseToLayers } from './utils';
import { useRasterSymbologyContext } from './RasterSymbologyContext';

export default function MapViewMode() {
  const { activeDataProduct, activeMapTool, activeProject } = useMapContext();
  const { mapboxAccessTokenDispatch, maptilerApiKeyDispatch } = useMapApiKeys();
  const {
    state: { layers },
    dispatch,
  } = useMapLayerContext();
  const symbologyContext = useRasterSymbologyContext();

  useEffect(() => {
    if (
      !import.meta.env.VITE_MAPBOX_ACCESS_TOKEN ||
      !import.meta.env.VITE_MAPTILER_API_KEY
    ) {
      fetch('/config.json')
        .then((response) => response.json())
        .then((config) => {
          if (config.mapboxAccessToken) {
            mapboxAccessTokenDispatch({
              type: 'set',
              payload: config.mapboxAccessToken,
            });
          }
          if (config.maptilerApiKey) {
            maptilerApiKeyDispatch({
              type: 'set',
              payload: config.maptilerApiKey,
            });
          }
        })
        .catch((error) => {
          console.error('Failed to load config.json:', error);
        });
    } else {
      if (import.meta.env.VITE_MAPBOX_ACCESS_TOKEN) {
        mapboxAccessTokenDispatch({
          type: 'set',
          payload: import.meta.env.VITE_MAPBOX_ACCESS_TOKEN,
        });
      }
      if (import.meta.env.VITE_MAPTILER_API_KEY) {
        maptilerApiKeyDispatch({
          type: 'set',
          payload: import.meta.env.VITE_MAPTILER_API_KEY,
        });
      }
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
    (activeDataProduct &&
      activeDataProduct.data_type !== 'point_cloud' &&
      activeDataProduct.data_type !== 'panoramic' &&
      activeDataProduct.data_type !== '3dgs')
  ) {
    return <HomeMap layers={layers} />;
  } else if (activeDataProduct.data_type === 'panoramic') {
    return <PanoViewer imageUrl={activeDataProduct.url} />;
  } else if (activeDataProduct.data_type === '3dgs') {
    return <ThreeDGSViewer imageUrl={activeDataProduct.url} />;
  } else {
    const copcPath = activeDataProduct.url;
    return <PotreeViewer copcPath={copcPath} />;
  }
}
