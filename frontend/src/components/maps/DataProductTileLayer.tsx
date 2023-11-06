import { TileLayer } from 'react-leaflet/TileLayer';

import { SymbologySettings, useMapContext } from './MapContext';

const dynamicTileService = '/cog/tiles/WebMercatorQuad/{z}/{x}/{y}@1x';

function getTileURL(
  url: string,
  cmap: string | undefined = undefined,
  scale: number[] | undefined = undefined,
  bidxs: number[] | undefined = undefined
): string {
  let tileURL = `${dynamicTileService}?url=${url}`;
  if (cmap) tileURL += `&colormap_name=${cmap}`;
  if (scale) tileURL += `&rescale=${scale.toString()}`;
  if (bidxs) tileURL += `&bidx=${bidxs[0]}&bidx=${bidxs[1]}&bidx=${bidxs[2]}`;
  return tileURL;
}

function getBandIdsFromUserStyle(user_style: SymbologySettings | null) {
  if (user_style) {
    return [
      user_style.blueBand ? user_style.blueBand : 1,
      user_style.greenBand ? user_style.greenBand : 2,
      user_style.redBand ? user_style.redBand : 3,
    ];
  } else {
    return [1, 2, 3];
  }
}

export default function DataProductTileLayer() {
  const { activeDataProduct, symbologySettings } = useMapContext();
  if (activeDataProduct) {
    let scale: number[] | undefined = undefined;
    let cmap: string = 'rainbow';
    if (activeDataProduct.data_type === 'dsm') {
      const stats = activeDataProduct.stac_properties.raster[0].stats;
      cmap = symbologySettings.colorRamp ? symbologySettings.colorRamp : 'rainbow';
      if (symbologySettings.minMax === 'userDefined') {
        scale = [
          symbologySettings.userMin ? symbologySettings.userMin : stats.minimum,
          symbologySettings.userMax ? symbologySettings.userMax : stats.maximum,
        ];
      } else if (symbologySettings.minMax === 'meanStdDev') {
        const multiplier = symbologySettings.meanStdDev
          ? symbologySettings.meanStdDev
          : 2;
        scale = [
          stats.mean - stats.stddev * multiplier,
          stats.mean + stats.stddev * multiplier,
        ];
      } else {
        scale = [
          symbologySettings.min ? symbologySettings.min : stats.minimum,
          symbologySettings.max ? symbologySettings.max : stats.maximum,
        ];
      }
      return (
        <TileLayer
          url={getTileURL(
            activeDataProduct.url.replace('http://localhost', ''),
            cmap,
            scale
          )}
          zIndex={500}
          maxNativeZoom={21}
          maxZoom={24}
        />
      );
    } else {
      return (
        <TileLayer
          url={getTileURL(
            activeDataProduct.url.replace('http://localhost', ''),
            undefined,
            undefined,
            getBandIdsFromUserStyle(symbologySettings)
          )}
          zIndex={500}
          maxNativeZoom={21}
          maxZoom={24}
        />
      );
    }
  } else {
    return null;
  }
}
