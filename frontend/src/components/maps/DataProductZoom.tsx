import { useEffect } from 'react';
import { useMap } from 'react-map-gl/maplibre';

import { useMapContext } from './MapContext';
import { NON_MAP_DATA_TYPES } from './LayerPane/utils';

export default function DataProductZoom() {
  const { current: map } = useMap();
  const { activeDataProduct } = useMapContext();

  useEffect(() => {
    if (!map || !activeDataProduct?.bbox) return;
    if ((NON_MAP_DATA_TYPES as readonly string[]).includes(activeDataProduct.data_type)) return;

    map.fitBounds(activeDataProduct.bbox, {
      padding: 20,
      duration: 1000,
    });
  }, [map, activeDataProduct]);

  return null;
}
