import 'maplibre-gl-lidar/style.css';
import { LidarControl } from 'maplibre-gl-lidar';
import { useEffect, useRef } from 'react';
import { useMap } from 'react-map-gl/maplibre';

import { DataProduct } from '../pages/workspace/projects/Project';

export default function ProjectPointCloudLayer({
  dataProduct,
}: {
  dataProduct: DataProduct;
}) {
  const { current: map } = useMap();
  const controlRef = useRef<LidarControl | null>(null);

  useEffect(() => {
    if (!map) return;

    const ctrl = new LidarControl({
      copcLoadingMode: 'dynamic',
      colorScheme: 'elevation',
      opacity: 1,
      pickable: true,
    });
    map.addControl(ctrl, 'top-left');
    ctrl.loadPointCloud(dataProduct.url);
    controlRef.current = ctrl;

    return () => {
      if (controlRef.current) {
        map.removeControl(controlRef.current);
        controlRef.current = null;
      }
    };
  }, [map, dataProduct.url]);

  return null;
}
