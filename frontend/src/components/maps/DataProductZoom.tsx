import { useEffect } from 'react';
import { useMap } from 'react-map-gl/maplibre';

import { useMapContext } from './MapContext';
import { NON_MAP_DATA_TYPES } from './LayerPane/utils';

export default function DataProductZoom() {
  const { current: map } = useMap();
  const { activeDataProduct, pointCloudViewer } = useMapContext();

  useEffect(() => {
    if (!map || !activeDataProduct?.bbox) return;

    const isNonMapType = (NON_MAP_DATA_TYPES as readonly string[]).includes(
      activeDataProduct.data_type
    );
    // Skip zoom for non-map types, but allow point clouds when displayed on the map
    if (
      isNonMapType &&
      !(
        activeDataProduct.data_type === 'point_cloud' &&
        pointCloudViewer === 'map'
      )
    ) {
      return;
    }

    map.fitBounds(activeDataProduct.bbox, {
      padding: 20,
      duration: 1000,
    });
  }, [map, activeDataProduct, pointCloudViewer]);

  return null;
}
