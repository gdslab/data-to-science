import { TileLayer } from 'react-leaflet/TileLayer';

import { useMapContext } from './MapContext';
import {
  DSMSymbologySettings,
  OrthoSymbologySettings,
  SymbologySettings,
} from './Maps';

import { DataProduct } from '../pages/workspace/projects/Project';
import { getDefaultStyle, isSingleBand } from './utils';

/**
 * Constructs URL for requesting tiles from TiTiler service.
 * @param {string} cmap Color map name.
 * @param {number[]} rescale Array of min/max rescale values for one or more bands.
 * @param {number[]} bidxs Array of band IDs.
 * @param {number} scale Tile size scale.
 * @param {string} dataProductId ID for data product that will be source of map tiles.
 * @returns {string} URL for requesting dynamic tiles from TiTiler service.
 */
function getTileURL(
  cmap: string | undefined = undefined,
  rescale: number[] | undefined = undefined,
  bidxs: number[] | undefined = undefined,
  scale: number = 2,
  dataProductId: string
): string {
  let queryParams = '';
  // Add band ids, color map, and rescale parameters to URL (if necessary)
  if (bidxs) queryParams += `&bidx=${bidxs[0]}&bidx=${bidxs[1]}&bidx=${bidxs[2]}`;
  if (cmap) queryParams += `&colormap_name=${cmap}`;
  if (rescale)
    rescale
      .reduce(
        (result: number[][], _, index, array) =>
          index % 2 === 0 ? [...result, array.slice(index, index + 2)] : result,
        []
      )
      .map((x) => `&rescale=${x}`)
      .forEach((rescaleValue) => (queryParams += rescaleValue));

  return `${
    import.meta.env.VITE_API_V1_STR
  }/public/maptiles?data_product_id=${dataProductId}&scale=${scale}${queryParams}&x={x}&y={y}&z={z}`;
}

/**
 * Looks up color ramp, calculates scale, and returns TileLayer for a data product.
 * @param {DataProduct} dataProduct Data product object.
 * @param {SymbologySettings} symbologySettings Symbology settings for a data product.
 * @returns {TileLayer} TileLayer for a data product.
 */
export function getDataProductTileLayer(
  dataProduct: DataProduct,
  symbologySettings?: SymbologySettings | undefined,
  tileLayerRef?: undefined | React.MutableRefObject<L.TileLayer | null>,
  scale: number = 2
) {
  if (isSingleBand(dataProduct)) {
    const stats = dataProduct.stac_properties.raster[0].stats;
    const symbology = symbologySettings as DSMSymbologySettings | undefined;
    const savedStyle = dataProduct.user_style
      ? (dataProduct.user_style as DSMSymbologySettings)
      : (getDefaultStyle(dataProduct) as DSMSymbologySettings);
    const colorRamp = symbology ? symbology.colorRamp : savedStyle.colorRamp;
    let rescale = [
      symbology ? symbology.min : savedStyle.min,
      symbology ? symbology.max : savedStyle.max,
    ];

    if (
      (symbology && symbology.mode === 'userDefined') ||
      (!symbology && savedStyle.mode === 'userDefined')
    ) {
      rescale = [
        symbology ? symbology.userMin : savedStyle.userMin,
        symbology ? symbology.userMax : savedStyle.userMax,
      ];
    }
    if (
      (symbology && symbology.mode === 'meanStdDev') ||
      (!symbology && savedStyle.mode === 'meanStdDev')
    ) {
      rescale = [
        stats.mean -
          stats.stddev * (symbology ? symbology.meanStdDev : savedStyle.meanStdDev),
        stats.mean +
          stats.stddev * (symbology ? symbology.meanStdDev : savedStyle.meanStdDev),
      ];
    }

    return (
      <TileLayer
        ref={tileLayerRef}
        url={getTileURL(colorRamp, rescale, undefined, scale, dataProduct.id)}
        zIndex={500}
        maxNativeZoom={24}
        maxZoom={26}
        opacity={
          symbology && symbology.opacity
            ? symbology.opacity / 100
            : savedStyle.opacity
            ? savedStyle.opacity
            : 1
        }
      />
    );
  } else {
    const symbology = symbologySettings as OrthoSymbologySettings | undefined;
    const savedStyle = dataProduct.user_style
      ? (dataProduct.user_style as OrthoSymbologySettings)
      : (getDefaultStyle(dataProduct) as OrthoSymbologySettings);

    const red = symbology ? symbology.red : savedStyle.red;
    const green = symbology ? symbology.green : savedStyle.green;
    const blue = symbology ? symbology.blue : savedStyle.blue;

    const bidxs = [red.idx, green.idx, blue.idx];
    const raster_props = dataProduct.stac_properties.raster;

    let rescale = [red.min, red.max, green.min, green.max, blue.min, blue.max];

    if (
      (symbology && symbology.mode === 'userDefined') ||
      (!symbology && savedStyle.mode === 'userDefined')
    ) {
      rescale = [
        red.userMin,
        red.userMax,
        green.userMin,
        green.userMax,
        blue.userMin,
        blue.userMax,
      ];
    }

    if (
      (symbology && symbology.mode === 'meanStdDev') ||
      (!symbology && savedStyle.mode === 'meanStdDev')
    ) {
      rescale = [
        raster_props[red.idx - 1].stats.mean -
          raster_props[red.idx - 1].stats.stddev *
            (symbology ? symbology.meanStdDev : savedStyle.meanStdDev),
        raster_props[red.idx - 1].stats.mean +
          raster_props[red.idx - 1].stats.stddev *
            (symbology ? symbology.meanStdDev : savedStyle.meanStdDev),
        raster_props[green.idx - 1].stats.mean -
          raster_props[green.idx - 1].stats.stddev *
            (symbology ? symbology.meanStdDev : savedStyle.meanStdDev),
        raster_props[green.idx - 1].stats.mean +
          raster_props[green.idx - 1].stats.stddev *
            (symbology ? symbology.meanStdDev : savedStyle.meanStdDev),
        raster_props[blue.idx - 1].stats.mean -
          raster_props[blue.idx - 1].stats.stddev *
            (symbology ? symbology.meanStdDev : savedStyle.meanStdDev),
        raster_props[blue.idx - 1].stats.mean +
          raster_props[blue.idx - 1].stats.stddev *
            (symbology ? symbology.meanStdDev : savedStyle.meanStdDev),
      ];
    }

    return (
      <TileLayer
        url={getTileURL(undefined, rescale, bidxs, scale, dataProduct.id)}
        zIndex={500}
        maxNativeZoom={24}
        maxZoom={26}
        opacity={
          symbology && symbology.opacity
            ? symbology.opacity / 100
            : savedStyle.opacity
            ? savedStyle.opacity
            : 1
        }
      />
    );
  }
}

export default function DataProductTileLayer({
  activeDataProduct,
  symbology = undefined,
  tileLayerRef = undefined,
}: {
  activeDataProduct: DataProduct;
  symbology?: OrthoSymbologySettings | DSMSymbologySettings | undefined;
  tileLayerRef?: undefined | React.MutableRefObject<L.TileLayer | null>;
}) {
  const { symbologySettings, tileScale } = useMapContext();

  if (!activeDataProduct) throw Error('No active data product');

  return getDataProductTileLayer(
    activeDataProduct,
    symbology ? symbology : symbologySettings,
    tileLayerRef,
    tileScale
  );
}

export function HillshadeTileLayer({
  dataProduct,
}: {
  dataProduct: DataProduct | null;
}) {
  if (!dataProduct) return null;

  if (!isSingleBand(dataProduct)) {
    return null;
  }

  const max = dataProduct.stac_properties.raster[0].stats.maximum;
  const min = dataProduct.stac_properties.raster[0].stats.minimum;

  return (
    <TileLayer
      url={getTileURL(undefined, [min, max], undefined, undefined, dataProduct.id)}
      zIndex={100}
      maxNativeZoom={24}
      maxZoom={26}
      opacity={1}
    />
  );
}
