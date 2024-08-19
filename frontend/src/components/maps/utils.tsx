import { DataProduct, Flight } from '../pages/projects/Project';
import { SymbologySettings } from './Maps';

function getDefaultStyle(dataProduct: DataProduct): SymbologySettings {
  if (isSingleBand(dataProduct)) {
    const stats = dataProduct.stac_properties.raster[0].stats;
    return {
      colorRamp: 'rainbow',
      max: stats.maximum,
      meanStdDev: 2,
      min: stats.minimum,
      mode: 'minMax',
      userMin: stats.minimum,
      userMax: stats.maximum,
      opacity: 100,
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
      opacity: 100,
    };
  }
}

function getHillshade(
  activeDataProduct: DataProduct,
  flights: Flight[]
): DataProduct | null {
  const dataProductName = activeDataProduct.data_type.toLowerCase();
  const filteredFlights = flights.filter(
    ({ id }) => id === activeDataProduct.flight_id
  );
  if (filteredFlights.length > 0 && filteredFlights[0].data_products.length > 1) {
    const dataProducts = filteredFlights[0].data_products;
    const dataProductHillshade = dataProducts.filter(
      (dataProduct) =>
        dataProduct.data_type.toLowerCase().split(' hs')[0] === dataProductName &&
        dataProduct.data_type.toLowerCase().split(' hs').length > 1
    );
    return dataProductHillshade.length > 0 ? dataProductHillshade[0] : null;
  } else {
    return null;
  }
}

/**
 * Returns true if data product has a single band.
 * @param dataProduct Active data product.
 * @returns True if single band, otherwise False.
 */
function isSingleBand(dataProduct: DataProduct): boolean {
  return dataProduct.stac_properties && dataProduct.stac_properties.raster.length === 1;
}

export { getDefaultStyle, getHillshade, isSingleBand };
