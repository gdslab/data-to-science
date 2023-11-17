import { TileLayer } from 'react-leaflet/TileLayer';

import {
  DSMSymbologySettings,
  OrthoSymbologySettings,
  useMapContext,
} from './MapContext';

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

export default function DataProductTileLayer() {
  const { activeDataProduct, symbologySettings } = useMapContext();

  if (!activeDataProduct) throw Error('No active data product');

  if (activeDataProduct.data_type === 'dsm') {
    const stats = activeDataProduct.stac_properties.raster[0].stats;
    const symbology = symbologySettings as DSMSymbologySettings;
    let scale = [symbology.min, symbology.max];

    if (symbology.mode === 'userDefined') {
      scale = [symbology.userMin, symbology.userMax];
    }
    if (symbology.mode === 'meanStdDev') {
      scale = [
        stats.mean - stats.stddev * symbology.meanStdDev,
        stats.mean + stats.stddev * symbology.meanStdDev,
      ];
    }

    return (
      <TileLayer
        url={getTileURL(
          activeDataProduct.url.replace('http://localhost', ''),
          symbology.colorRamp,
          scale
        )}
        zIndex={500}
        maxNativeZoom={21}
        maxZoom={24}
      />
    );
  } else {
    const symbology = symbologySettings as OrthoSymbologySettings;
    const bidxs = [symbology.red.idx, symbology.green.idx, symbology.blue.idx];
    const scale = [
      symbology.red.min,
      symbology.red.max,
      symbology.green.min,
      symbology.green.max,
      symbology.blue.min,
      symbology.blue.max,
    ];

    return (
      <TileLayer
        url={getTileURL(
          activeDataProduct.url.replace('http://localhost', ''),
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
