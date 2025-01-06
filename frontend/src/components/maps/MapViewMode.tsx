import { useEffect } from 'react';

import { useMapContext } from './MapContext';
import CompareMap from './CompareMap';
import HomeMap from './HomeMap';
import PotreeViewer from './PotreeViewer';

export default function MapViewMode() {
  const { activeDataProduct, activeMapTool, mapboxAccessTokenDispatch } =
    useMapContext();

  useEffect(() => {
    if (!import.meta.env.VITE_MAPBOX_ACCESS_TOKEN) {
      fetch('/config.json')
        .then((response) => response.json())
        .then((config) => {
          mapboxAccessTokenDispatch({ type: 'set', payload: config.mapboxAccessToken });
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

  if (activeMapTool === 'compare') {
    return <CompareMap />;
  } else if (
    !activeDataProduct ||
    (activeDataProduct && activeDataProduct.data_type !== 'point_cloud')
  ) {
    return <HomeMap />;
  } else {
    const copcPath = activeDataProduct.url;
    return <PotreeViewer copcPath={copcPath} />;
  }
}
