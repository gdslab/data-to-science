import { DataProduct } from '../pages/projects/ProjectDetail';
import { SymbologySettings } from './MapContext';

function getDefaultStyle(dataProduct: DataProduct): SymbologySettings {
  if (
    dataProduct.data_type === 'dsm' ||
    (dataProduct.stac_properties && dataProduct.stac_properties.raster.length === 1)
  ) {
    const stats = dataProduct.stac_properties.raster[0].stats;
    return {
      colorRamp: 'rainbow',
      max: stats.maximum,
      meanStdDev: 2,
      min: stats.minimum,
      mode: 'minMax',
      userMin: stats.minimum,
      userMax: stats.maximum,
    };
  } else {
    const raster = dataProduct.stac_properties.raster;
    return {
      mode: 'minMax',
      meanStdDev: 2,
      red: {
        idx: 1,
        min: raster[0].stats.minimum,
        max: raster[0].stats.maximum,
        userMin: raster[0].stats.minimum,
        userMax: raster[0].stats.maximum,
      },
      green: {
        idx: 2,
        min: raster[1].stats.minimum,
        max: raster[1].stats.maximum,
        userMin: raster[1].stats.minimum,
        userMax: raster[1].stats.maximum,
      },
      blue: {
        idx: 3,
        min: raster[2].stats.minimum,
        max: raster[2].stats.maximum,
        userMin: raster[2].stats.minimum,
        userMax: raster[2].stats.maximum,
      },
    };
  }
}

export { getDefaultStyle };
