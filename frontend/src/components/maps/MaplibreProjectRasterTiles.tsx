import { useMemo } from 'react';
import { Layer, Source, useMap } from 'react-map-gl/maplibre';

import { DataProduct } from '../pages/projects/Project';
import {
  SingleBandSymbology,
  MultibandSymbology,
  useRasterSymbologyContext,
} from './RasterSymbologyContext';

import { getMultibandMinMax, getSingleBandMinMax, isSingleBand } from './utils';

function constructRasterTileUrl(
  dataProduct: DataProduct,
  symbologySettings: SingleBandSymbology | MultibandSymbology | null
): string {
  if (!symbologySettings) return '';

  // path to data product
  const cogUrl = dataProduct.filepath;

  // tile matrix set
  const tms = 'WebMercatorQuad';

  // parts of path for fetching tiles
  const resourcePath = `/cog/tiles/${tms}/{z}/{x}/{y}@2x`;
  const basePath = import.meta.env.VITE_BASE_URL || window.location.origin;

  const queryParams = new URLSearchParams();
  queryParams.append('url', cogUrl);

  if (isSingleBand(dataProduct)) {
    const symbology = symbologySettings as SingleBandSymbology;

    queryParams.append('bidx', '1');
    queryParams.append('colormap_name', symbology.colorRamp);
    queryParams.append(
      'rescale',
      getSingleBandMinMax(dataProduct.stac_properties, symbology).flat().join(',')
    );
  } else {
    const symbology = symbologySettings as MultibandSymbology;
    queryParams.append('bidx', symbology.red.idx.toString());
    queryParams.append('bidx', symbology.green.idx.toString());
    queryParams.append('bidx', symbology.blue.idx.toString());
    getMultibandMinMax(dataProduct.stac_properties, symbology).forEach((rescale) => {
      queryParams.append('rescale', `${rescale}`);
    });
  }

  // add data product id and add signature
  queryParams.append('dataProductId', dataProduct.id);
  queryParams.append('expires', (dataProduct.signature?.expires || 0).toString());
  queryParams.append('secure', dataProduct.signature?.secure || '');

  // add query params to base url
  const url = `${basePath}${resourcePath}?${queryParams.toString()}`;

  return url;
}

export default function MaplibreProjectRasterTiles({
  dataProduct,
}: {
  dataProduct: DataProduct;
}) {
  const { current: map } = useMap();

  const { state } = useRasterSymbologyContext();

  const { isLoaded, symbology } = state[dataProduct.id] || {};

  const tiles = useMemo(
    () => [constructRasterTileUrl(dataProduct, symbology)],
    [dataProduct, symbology]
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
    >
      <Layer
        key={`${dataProduct.id}-layer`}
        id={dataProduct.id}
        type="raster"
        source={dataProduct.id}
        paint={{
          'raster-opacity': symbology.opacity ? symbology.opacity / 100 : 1,
        }}
      />
    </Source>
  );
}
