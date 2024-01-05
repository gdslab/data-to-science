import { TileLayer } from 'react-leaflet/TileLayer';

import {
  DSMSymbologySettings,
  OrthoSymbologySettings,
  SymbologySettings,
  useMapContext,
} from './MapContext';
import { DataProduct } from '../pages/projects/ProjectDetail';
import { getDefaultStyle } from './utils';

/**
 * Constructs URL for requesting tiles from TiTiler service.
 * @param {string} url URL for Cloud Optimized GeoTIFF.
 * @param {string} cmap Color map name.
 * @param {number[]} scale Array of min/max rescale values for one or more bands.
 * @param {number[]} bidxs Array of band IDs.
 * @returns {string} URL for requesting dynamic tiles from TiTiler service.
 */
function getTileURL(
  url: string,
  cmap: string | undefined = undefined,
  scale: number[] | undefined = undefined,
  bidxs: number[] | undefined = undefined
): string {
  // URL for TiTIler service
  let titilerURL = `/cog/tiles/WebMercatorQuad/{z}/{x}/{y}@1x?url=${url}`;
  // Add band ids, color map, and rescale parameters to URL (if necessary)
  if (bidxs) titilerURL += `&bidx=${bidxs[0]}&bidx=${bidxs[1]}&bidx=${bidxs[2]}`;
  if (cmap) titilerURL += `&colormap_name=${cmap}`;
  if (scale)
    scale
      .reduce(
        (result: number[][], _, index, array) =>
          index % 2 === 0 ? [...result, array.slice(index, index + 2)] : result,
        []
      )
      .map((x) => `&rescale=${x}`)
      .forEach((rescale) => (titilerURL += rescale));

  return titilerURL;
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
  tileLayerRef?: undefined | React.MutableRefObject<L.TileLayer | null>
) {
  if (dataProduct.data_type === 'dsm') {
    const stats = dataProduct.stac_properties.raster[0].stats;
    const symbology = symbologySettings as DSMSymbologySettings | undefined;
    const savedStyle = dataProduct.user_style
      ? (dataProduct.user_style as DSMSymbologySettings)
      : (getDefaultStyle(dataProduct) as DSMSymbologySettings);
    const colorRamp = symbology ? symbology.colorRamp : savedStyle.colorRamp;
    let scale = [
      symbology ? symbology.min : savedStyle.min,
      symbology ? symbology.max : savedStyle.max,
    ];

    if (
      (symbology && symbology.mode === 'userDefined') ||
      (!symbology && savedStyle.mode === 'userDefined')
    ) {
      scale = [
        symbology ? symbology.userMin : savedStyle.userMin,
        symbology ? symbology.userMax : savedStyle.userMax,
      ];
    }
    if (
      (symbology && symbology.mode === 'meanStdDev') ||
      (!symbology && savedStyle.mode === 'meanStdDev')
    ) {
      scale = [
        stats.mean -
          stats.stddev * (symbology ? symbology.meanStdDev : savedStyle.meanStdDev),
        stats.mean +
          stats.stddev * (symbology ? symbology.meanStdDev : savedStyle.meanStdDev),
      ];
    }

    return (
      <TileLayer
        ref={tileLayerRef}
        url={getTileURL(
          dataProduct.url.replace(import.meta.env.VITE_DOMAIN, ''),
          colorRamp,
          scale
        )}
        zIndex={500}
        maxNativeZoom={21}
        maxZoom={24}
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

    let scale = [red.min, red.max, green.min, green.max, blue.min, blue.max];

    if (
      (symbology && symbology.mode === 'userDefined') ||
      (!symbology && savedStyle.mode === 'userDefined')
    ) {
      scale = [
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
      scale = [
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
        url={getTileURL(
          dataProduct.url.replace(import.meta.env.VITE_DOMAIN, ''),
          undefined,
          scale,
          bidxs
        )}
        zIndex={500}
        maxNativeZoom={21}
        maxZoom={24}
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
  const { symbologySettings } = useMapContext();

  if (!activeDataProduct) throw Error('No active data product');

  return getDataProductTileLayer(
    activeDataProduct,
    symbology ? symbology : symbologySettings,
    tileLayerRef
  );
}
