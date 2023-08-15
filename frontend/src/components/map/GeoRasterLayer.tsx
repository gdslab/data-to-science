import * as React from 'react';
import parseGeoraster from 'georaster';
import GeoRasterLayerForLeaflet from 'georaster-layer-for-leaflet';
import type { GeoRasterLayerOptions, GeoRaster } from 'georaster-layer-for-leaflet';
import { createPathComponent } from '@react-leaflet/core';
import type { LeafletContextInterface } from '@react-leaflet/core';

const GeoRasterComponent = createPathComponent(
  (options: GeoRasterLayerOptions, context: LeafletContextInterface) => {
    // zoom map to layer
    const layer = new GeoRasterLayerForLeaflet(options);
    // context.map.fitBounds(layer.getBounds());
    return {
      instance: layer,
      context,
    };
  }
);

const useGeoraster = (paths: string[]) => {
  const [georasters, setGeoraster] = React.useState<GeoRaster[]>();

  React.useEffect(() => {
    const promises = paths.map((path) => parseGeoraster(path));
    Promise.all([...promises])
      .then((res: GeoRaster[]) => {
        setGeoraster(res);
      })
      .catch((err) => {
        console.error('Error loading a Georaster in GeoRasterLayer.tsx', err);
      });
  }, [paths]);

  return georasters;
};

type Props = {
  paths: string[];
} & Omit<GeoRasterLayerOptions, 'georaster' | 'georasters'>;

function GeoRasterLayer({ paths, ...options }: Props): React.ReactElement | null {
  console.log('GeoRasterLayer');
  const georasters = useGeoraster(paths);

  return georasters ? (
    <GeoRasterComponent {...options} georasters={georasters} />
  ) : null;
}

export default GeoRasterLayer;
