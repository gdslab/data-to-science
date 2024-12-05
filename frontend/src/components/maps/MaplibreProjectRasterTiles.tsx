import { Layer, Source, useMap } from 'react-map-gl/maplibre';
import { DataProduct, STACProperties } from '../pages/projects/Project';

import {
  SingleBandSymbology,
  MultiBandSymbology,
  useRasterSymbologyContext,
} from './RasterSymbologyContext';
import { isSingleBand } from './utils';
import { useMemo } from 'react';

function getDsmMinMax(
  stacProps: STACProperties,
  symbology: SingleBandSymbology
): [number, number] {
  const defaultMinMax: [number, number] = [0, 255];

  switch (symbology.mode) {
    case 'minMax':
      if (symbology.min === undefined || symbology.max === undefined) {
        console.warn(
          'Min and max raster props missing, falling back to default min/max.'
        );
        return defaultMinMax;
      }
      return [symbology.min, symbology.max];

    case 'userDefined':
      if (symbology.userMin === undefined || symbology.userMax === undefined) {
        console.warn(
          'User defined min and max props missing, falling back to default min/max.'
        );
        return defaultMinMax;
      }
      return [symbology.userMin, symbology.userMax];

    case 'meanStdDev':
      const stats = stacProps.raster?.[0]?.stats;
      if (!stats || stats.mean === undefined || stats.stddev === undefined) {
        console.warn('Stats missing, falling back to default min/max.');
        return defaultMinMax;
      }
      const deviation = stats.stddev * symbology.meanStdDev;
      return [stats.mean - deviation, stats.mean + deviation];

    default:
      console.warn(`Unexpected symbology mode: ${symbology.mode}`);
      return defaultMinMax;
  }
}

function getOrthoMinMax(
  stacProps: STACProperties,
  symbology: MultiBandSymbology
): [[number, number], [number, number], [number, number]] {
  const defaultMinMax: [[number, number], [number, number], [number, number]] = [
    [0, 255],
    [0, 255],
    [0, 255],
  ];

  const validateBands = (key: 'min' | 'max' | 'userMin' | 'userMax') =>
    ['red', 'green', 'blue'].every((band) => symbology[band]?.[key] !== undefined);

  const getStats = (index: number) => stacProps.raster?.[index - 1]?.stats;

  switch (symbology.mode) {
    case 'minMax':
      if (!validateBands('min') || !validateBands('max')) {
        console.warn(
          'Min and max raster props missing for at least one band, falling back to default min/max.'
        );
        return defaultMinMax;
      } else {
        return [
          [symbology.red.min, symbology.red.max],
          [symbology.green.min, symbology.green.max],
          [symbology.blue.min, symbology.blue.max],
        ];
      }

    case 'userDefined':
      if (!validateBands('userMin') || !validateBands('userMax')) {
        console.warn(
          'User defined min and max props missing for at least one band, falling back to default min/max.'
        );
        return defaultMinMax;
      } else {
        return [
          [symbology.red.userMin, symbology.red.userMax],
          [symbology.green.userMin, symbology.green.userMax],
          [symbology.blue.userMin, symbology.blue.userMax],
        ];
      }

    case 'meanStdDev':
      // verify we have a band index for RGB
      if (
        !['red', 'green', 'blue'].every((band) => symbology[band]?.idx !== undefined)
      ) {
        console.warn(
          'Missing index for at least one band, falling back to default min/max.'
        );
        return defaultMinMax;
      } else {
        const stats = ['red', 'green', 'blue'].map((band) =>
          getStats(symbology[band].idx)
        );

        // verify we have a mean, std. dev. for each band and a meanStdDev mult factor
        if (
          stats.some((s) => !s || s.mean === undefined || s.stddev === undefined) ||
          symbology.meanStdDev === undefined
        ) {
          console.warn(
            'Stats missing for at least one band, falling back to default min/max.'
          );
          return defaultMinMax;
        }

        return stats.map((stat) => {
          const deviation = stat.stddev * symbology.meanStdDev;
          return [stat.mean - deviation, stat.mean + deviation];
        }) as [[number, number], [number, number], [number, number]];
      }

    default:
      return defaultMinMax;
  }
}

function constructRasterTileUrl(
  dataProduct: DataProduct,
  symbologySettings: SingleBandSymbology | MultiBandSymbology | null
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
      getDsmMinMax(dataProduct.stac_properties, symbology).flat().join(',')
    );
  } else {
    const symbology = symbologySettings as MultiBandSymbology;
    queryParams.append('bidx', symbology.red.idx.toString());
    queryParams.append('bidx', symbology.green.idx.toString());
    queryParams.append('bidx', symbology.blue.idx.toString());
    getOrthoMinMax(dataProduct.stac_properties, symbology).forEach((rescale) => {
      queryParams.append('rescale', `${rescale}`);
    });
  }

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

  const { isLoaded, symbology } = state[dataProduct.id];

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
