import { FeatureCollection, Point, Polygon } from 'geojson';

import {
  DataProduct,
  Flight,
  MapLayer,
  STACProperties,
} from '../pages/projects/Project';
import { SingleBandSymbology, MultiBandSymbology } from './RasterSymbologyContext';

type Bounds = [number, number, number, number];

/**
 * Calculates bounding box for features in GeoJSON Feature Collection. Supports
 * Point or Polygon geometry types.
 * @param geojsonData Feature Collection of Point or Polygon Feautres.
 * @returns Bounding box array.
 */
function calculateBoundsFromGeoJSON(
  geojsonData: FeatureCollection<Point | Polygon>
): Bounds {
  const bounds: Bounds = geojsonData.features.reduce(
    (bounds, feature) => {
      const [minLng, minLat, maxLng, maxLat] = bounds;

      if (feature.geometry.type === 'Polygon') {
        // Flatten the coordinates array into single array of coordinates
        const coordinates = feature.geometry.coordinates.flat(Infinity) as number[];

        for (let i = 0; i < coordinates.length; i += 2) {
          const lng = coordinates[i];
          const lat = coordinates[i + 1];
          bounds[0] = Math.min(bounds[0], lng);
          bounds[1] = Math.min(bounds[1], lat);
          bounds[2] = Math.max(bounds[2], lng);
          bounds[3] = Math.max(bounds[3], lat);
        }

        return bounds;
      } else if (feature.geometry.type === 'Point') {
        const [lng, lat] = feature.geometry.coordinates;
        return [
          Math.min(minLng, lng),
          Math.min(minLat, lat),
          Math.max(maxLng, lng),
          Math.max(maxLat, lat),
        ];
      } else {
        throw new Error('Unable to calculate bounds for GeoJSON data');
      }
    },
    [Infinity, Infinity, -Infinity, -Infinity]
  );

  return bounds;
}

/**
 * Map API response with project vector layers to MapLayer[].
 * @param layers Vector layers returned from API response.
 * @returns Mapped vector layers.
 */
const mapApiResponseToLayers = (layers: MapLayer[]) =>
  layers.map((layer) => ({
    id: layer.layer_id,
    name: layer.layer_name,
    checked: false,
    type: layer.geom_type,
    color: '#ffde21',
    opacity: 100,
    signedUrl: layer.signed_url,
  }));

function getDefaultStyle(
  dataProduct: DataProduct
): SingleBandSymbology | MultiBandSymbology {
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

/**
 * Returns object with default symbology properties for a single-band data product.
 * @param stacProperties Data product band statistics.
 * @returns Default symbology.
 */
const createDefaultSingleBandSymbology = (
  stacProperties: STACProperties
): SingleBandSymbology => ({
  colorRamp: 'rainbow',
  meanStdDev: 2,
  mode: 'minMax',
  opacity: 100,
  min: stacProperties.raster[0].stats.minimum,
  max: stacProperties.raster[0].stats.maximum,
  userMin: stacProperties.raster[0].stats.minimum,
  userMax: stacProperties.raster[0].stats.maximum,
});

/**
 * Returns object with default symbology properties for a 3-band data product.
 * @param stacProperties Data product band statistics.
 * @returns Default symbology.
 */
const createDefaultMultiBandSymbology = (
  stacProperties: STACProperties
): MultiBandSymbology => {
  const createColorChannel = (idx: number) => ({
    idx,
    min: stacProperties.raster[idx - 1].stats.minimum,
    max: stacProperties.raster[idx - 1].stats.maximum,
    userMin: stacProperties.raster[idx - 1].stats.minimum,
    userMax: stacProperties.raster[idx - 1].stats.maximum,
  });

  return {
    meanStdDev: 2,
    mode: 'minMax',
    opacity: 100,
    red: createColorChannel(1),
    green: createColorChannel(2),
    blue: createColorChannel(3),
  };
};

export {
  calculateBoundsFromGeoJSON,
  createDefaultSingleBandSymbology,
  createDefaultMultiBandSymbology,
  getDefaultStyle,
  getHillshade,
  isSingleBand,
  mapApiResponseToLayers,
};
