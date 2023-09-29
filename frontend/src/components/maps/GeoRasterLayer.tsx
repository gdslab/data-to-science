import * as React from 'react';
import parseGeoraster from 'georaster';
import GeoRasterLayerForLeaflet from 'georaster-layer-for-leaflet';
import type { GeoRasterLayerOptions, GeoRaster } from 'georaster-layer-for-leaflet';
import { createPathComponent } from '@react-leaflet/core';
import type { LeafletContextInterface } from '@react-leaflet/core';

import { setPixelColors } from './utils';

const GeoRasterComponent = createPathComponent(
  (options: GeoRasterLayerOptions, context: LeafletContextInterface) => {
    const {
      activeDataProduct = {},
      symbologySettings = {},
      ...layerOptions
    } = { ...options };

    // try {
    //   const options = {
    //     left: layerOptions.georasters[0].xmin,
    //     top: layerOptions.georasters[0].ymax,
    //     right: layerOptions.georasters[0].xmax,
    //     bottom: layerOptions.georasters[0].ymin,
    //     width: layerOptions.georasters[0].width,
    //     height: layerOptions.georasters[0].height,
    //   };
    //   layerOptions.georasters[0].getValues(options).then((values) => {
    //     // do something
    //   });
    // } catch (err) {
    //   console.error(err);
    // }

    // zoom map to layer
    const layer = new GeoRasterLayerForLeaflet({
      ...layerOptions,
      pixelValuesToColorFn: (values) =>
        setPixelColors(
          values,
          activeDataProduct ? activeDataProduct.stac_properties.raster : [],
          symbologySettings
        ),
    });
    context.map.fitBounds(layer.getBounds(), { maxZoom: 16 });
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
  const georasters = useGeoraster(paths);
  return georasters ? (
    <GeoRasterComponent {...options} georasters={georasters} />
  ) : null;
}

export default GeoRasterLayer;
