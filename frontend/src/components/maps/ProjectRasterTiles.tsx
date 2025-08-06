import { useMemo } from 'react';
import { Layer, Source, useMap } from 'react-map-gl/maplibre';

import { DataProduct } from '../pages/workspace/projects/Project';
import {
  SingleBandSymbology,
  MultibandSymbology,
  useRasterSymbologyContext,
} from './RasterSymbologyContext';

import { getTitilerQueryParams } from './utils';
import { useMapContext } from './MapContext';

function constructRasterTileUrl(
  dataProduct: DataProduct,
  symbologySettings: SingleBandSymbology | MultibandSymbology | null,
  tileScale: number
): string {
  if (!symbologySettings) return '';

  // path to data product
  const cogUrl = dataProduct.filepath;

  // tile matrix set
  const tms = 'WebMercatorQuad';

  // parts of path for fetching tiles
  const resourcePath = `/cog/tiles/${tms}/{z}/{x}/{y}@${tileScale}x`;
  const basePath = window.location.origin;
  const queryParams = getTitilerQueryParams(
    cogUrl,
    dataProduct,
    symbologySettings
  );
  // add query params to base url
  const url = `${basePath}${resourcePath}?${queryParams.toString()}`;

  return url;
}

export default function ProjectRasterTiles({
  boundingBox = undefined,
  dataProduct,
}: {
  boundingBox?: [number, number, number, number];
  dataProduct: DataProduct;
}) {
  const { current: map } = useMap();

  const { activeDataProduct, tileScale } = useMapContext();

  const { state } = useRasterSymbologyContext();

  const { isLoaded, symbology } = state[dataProduct.id] || {};

  const tiles = useMemo(
    () => [constructRasterTileUrl(dataProduct, symbology, tileScale)],
    [dataProduct, symbology, tileScale]
  );

  if (!symbology || !isLoaded || !map || !tiles) return null;

  return (
    <Source
      key={`${dataProduct.id}-source`}
      id={dataProduct.id}
      type="raster"
      tiles={tiles}
      maxzoom={24}
      minzoom={0}
      tileSize={256}
      {...(boundingBox ? { bounds: boundingBox } : {})}
    >
      <Layer
        key={`${dataProduct.id}-layer`}
        id={dataProduct.id}
        type="raster"
        source={dataProduct.id}
        paint={{
          'raster-opacity':
            symbology.opacity != null ? symbology.opacity / 100 : 1,
        }}
        beforeId={
          dataProduct.id !== activeDataProduct?.id
            ? activeDataProduct?.id
            : undefined
        }
      />
    </Source>
  );
}
