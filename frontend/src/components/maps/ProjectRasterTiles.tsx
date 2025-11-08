import { useMemo } from 'react';
import { Layer, Source, useMap } from 'react-map-gl/maplibre';

import { DataProduct } from '../pages/projects/Project';
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
  beforeLayerId = null,
  boundingBox = undefined,
  dataProduct,
}: {
  beforeLayerId?: string | null;
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

  // Determine the beforeId, but only use it if the layer actually exists in the map
  const safeBeforeId = useMemo(() => {
    if (!map) return undefined;

    // Try the provided beforeLayerId first
    if (beforeLayerId && map.getLayer(beforeLayerId)) {
      return beforeLayerId;
    }

    // Fallback to activeDataProduct if this is not the active one
    if (
      dataProduct.id !== activeDataProduct?.id &&
      activeDataProduct?.id &&
      map.getLayer(activeDataProduct.id)
    ) {
      return activeDataProduct.id;
    }

    // No valid beforeId found, render on top
    return undefined;
  }, [map, beforeLayerId, dataProduct.id, activeDataProduct?.id]);

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
        beforeId={safeBeforeId}
      />
    </Source>
  );
}
