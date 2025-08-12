import {
  Feature,
  FeatureCollection,
  Geometry,
  GeoJsonProperties,
  Point,
  Polygon,
} from 'geojson';
import maplibregl, { Map } from 'maplibre-gl';

import {
  DataProduct,
  Flight,
  MapLayer,
  ProjectFeatureCollection,
  STACProperties,
} from '../pages/workspace/projects/Project';
import { Project } from '../pages/workspace/projects/ProjectList';
import {
  SingleBandSymbology,
  MultibandSymbology,
} from './RasterSymbologyContext';

type Bounds = [number, number, number, number];

/**
 * Calculates bounding box for features in GeoJSON Feature Collection. Supports
 * Point or Polygon geometry types.
 * @param geojsonData Feature Collection of Point or Polygon Feautres.
 * @returns Bounding box array.
 */
function calculateBoundsFromGeoJSON(
  geojsonData: ProjectFeatureCollection | FeatureCollection<Point | Polygon>
): Bounds {
  const bounds: Bounds = geojsonData.features.reduce(
    (bounds, feature) => {
      const [minLng, minLat, maxLng, maxLat] = bounds;

      if (feature.geometry.type === 'Polygon') {
        // Flatten the coordinates array into single array of coordinates
        const coordinates = feature.geometry.coordinates.flat(
          Infinity
        ) as number[];

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
): SingleBandSymbology | MultibandSymbology {
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
  if (
    filteredFlights.length > 0 &&
    filteredFlights[0].data_products.length > 1
  ) {
    const dataProducts = filteredFlights[0].data_products;
    const dataProductHillshade = dataProducts.filter(
      (dataProduct) =>
        dataProduct.data_type.toLowerCase().split(' hs')[0] ===
          dataProductName &&
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
  return (
    dataProduct.stac_properties &&
    dataProduct.stac_properties.raster.length === 1
  );
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
const createDefaultMultibandSymbology = (
  stacProperties: STACProperties
): MultibandSymbology => {
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

/**
 * Returns default min/max values for single band raster.
 * @param stacProps STAC metadata for raster band.
 * @param symbology Current symbology settings.
 * @returns Min/max values for single band.
 */
const getSingleBandMinMax = (
  stacProps: STACProperties,
  symbology: SingleBandSymbology
): [number, number] => {
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
};

/**
 * Returns default min/max values for multiband raster.
 * @param stacProps STAC metadata for raster bands.
 * @param symbology Current symbology settings.
 * @returns Min/max values for each band.
 */
const getMultibandMinMax = (
  stacProps: STACProperties,
  symbology: MultibandSymbology
): [[number, number], [number, number], [number, number]] => {
  const defaultMinMax: [[number, number], [number, number], [number, number]] =
    [
      [0, 255],
      [0, 255],
      [0, 255],
    ];

  const validateBands = (key: 'min' | 'max' | 'userMin' | 'userMax') =>
    ['red', 'green', 'blue'].every(
      (band) => symbology[band]?.[key] !== undefined
    );

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
        !['red', 'green', 'blue'].every(
          (band) => symbology[band]?.idx !== undefined
        )
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
          stats.some(
            (s) => !s || s.mean === undefined || s.stddev === undefined
          ) ||
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
};

/**
 * Checks local storage for previously stored projects.
 * @returns Array of projects retrieved from local storage.
 */
function getLocalStorageProjects(): Project[] | null {
  if ('projects' in localStorage) {
    const lsProjectsString = localStorage.getItem('projects');
    if (lsProjectsString) {
      const lsProjects: Project[] = JSON.parse(lsProjectsString);
      if (lsProjects && lsProjects.length > 0) {
        return lsProjects;
      }
    }
  }

  return null;
}

/**
 * Returns query parameters for titiler /cog endpoint.
 * @param dataProduct Active data product.
 * @param symbology Symbology for active data product.
 * @param queryParams Current query parameters.
 * @returns Query parameters updated with symbology.
 */
function getTitilerQueryParams(
  cogUrl: string,
  dataProduct: DataProduct,
  symbology: SingleBandSymbology | MultibandSymbology
): URLSearchParams {
  const queryParams = new URLSearchParams();
  queryParams.append('url', cogUrl);

  if (isSingleBand(dataProduct)) {
    const s = symbology as SingleBandSymbology;

    queryParams.append('bidx', '1');
    queryParams.append('colormap_name', s.colorRamp);
    queryParams.append(
      'rescale',
      getSingleBandMinMax(dataProduct.stac_properties, s).flat().join(',')
    );
  } else {
    const s = symbology as MultibandSymbology;
    queryParams.append('bidx', s.red.idx.toString());
    queryParams.append('bidx', s.green.idx.toString());
    queryParams.append('bidx', s.blue.idx.toString());
    getMultibandMinMax(dataProduct.stac_properties, s).forEach((rescale) => {
      queryParams.append('rescale', `${rescale}`);
    });
  }

  // add data product id and add signature
  queryParams.append('dataProductId', dataProduct.id);
  queryParams.append(
    'expires',
    (dataProduct.signature?.expires || 0).toString()
  );
  queryParams.append('secure', dataProduct.signature?.secure || '');

  return queryParams;
}

/**
 * Sort projects by unique UUID string.
 * @param projects Array of projects with unique `id` strings.
 * @returns Array of sorted projects.
 */
function sortProjects(projects: Project[]): Project[] {
  return projects.slice().sort((a, b) => a.id.localeCompare(b.id));
}

/**
 * Compare projects currently stored in local storage with new projects returned
 * from API request.
 * @param oldProjects Array of projects currently in local storage.
 * @param newProjects Array of projects returned from API request.
 * @returns True if both arrays match, otherwise false.
 */
function areProjectsEqual(
  oldProjects: Project[],
  newProjects: Project[]
): boolean {
  const sortedOld = sortProjects(oldProjects);
  const sortedNew = sortProjects(newProjects);
  return JSON.stringify(sortedOld) === JSON.stringify(sortedNew);
}

/**
 * Sets projects returned from API in local storage. If projects already exist
 * in local storage, they will only be replaced if the projects returned from
 * the API differ.
 * @param projects Projects returned from API.
 */
function setLocalStorageProjects(projects: Project[]): void {
  const projectsString = JSON.stringify(projects);
  const storedProjects = getLocalStorageProjects();

  if (storedProjects) {
    // Compare stored data with the new projects
    if (!areProjectsEqual(storedProjects, projects)) {
      localStorage.setItem('projects', projectsString);
    }
  } else {
    // If nothing is stored, set the projects
    localStorage.setItem('projects', projectsString);
  }
}

/**
 * Returns the category of a value based on predefined thresholds for flights or data products.
 * @param count Value to be categorized.
 * @param type Type of count ('flight' or 'data_product').
 * @returns Category of the value.
 */
function getCategory(
  count: number,
  type: 'flight' | 'data_product'
): 'low' | 'medium' | 'high' {
  if (type === 'flight') {
    if (count >= 0 && count < 3) return 'low';
    else if (count >= 3 && count < 5) return 'medium';
    else return 'high';
  } else {
    // data_product type
    if (count >= 0 && count < 5) return 'low';
    else if (count >= 5 && count < 10) return 'medium';
    else return 'high';
  }
}

/**
 * Returns true if data product is an elevation data product.
 * @param dataProduct Data product to check.
 * @returns True if data product is an elevation data product, otherwise false.
 */
const isElevationDataProduct = (dataProduct: DataProduct): boolean => {
  const dataType = dataProduct.data_type.toLowerCase();
  return (
    (dataType.includes('dem') ||
      dataType.includes('dtm') ||
      dataType.includes('dsm')) &&
    isSingleBand(dataProduct)
  );
};

/**
 * Fit a MapLibre map view to the bounds of a GeoJSON Feature or Geometry.
 *
 * @param map - The MapLibre GL map instance
 * @param geo - A GeoJSON Feature or Geometry object
 * @param padding - Optional padding in pixels (default: 40)
 * @param duration - Optional animation duration in ms (default: 500)
 */
const fitMapToGeoJSON = (
  map: Map,
  geo: Geometry | Feature<Geometry, GeoJsonProperties> | FeatureCollection,
  padding = 40,
  duration = 500
) => {
  const bounds = new maplibregl.LngLatBounds();

  const pushCoord = (c: number[]) => {
    if (Array.isArray(c) && c.length >= 2) {
      bounds.extend([c[0], c[1]]);
    }
  };

  const extendFromGeometry = (geometry: Geometry) => {
    switch (geometry.type) {
      case 'Point':
        pushCoord(geometry.coordinates as number[]);
        break;
      case 'MultiPoint':
      case 'LineString':
        (geometry.coordinates as number[][]).forEach(pushCoord);
        break;
      case 'MultiLineString':
      case 'Polygon':
        (geometry.coordinates as number[][][]).forEach((ring) =>
          ring.forEach(pushCoord)
        );
        break;
      case 'MultiPolygon':
        (geometry.coordinates as number[][][][]).forEach((poly) =>
          poly.forEach((ring) => ring.forEach(pushCoord))
        );
        break;
      default:
        console.warn('Unsupported geometry type:', geometry.type);
    }
  };

  if ('type' in geo) {
    if (geo.type === 'Feature') {
      extendFromGeometry(geo.geometry);
    } else if (geo.type === 'FeatureCollection') {
      geo.features.forEach((f) => extendFromGeometry(f.geometry));
    } else {
      extendFromGeometry(geo as Geometry);
    }
  }

  if (!bounds.isEmpty()) {
    map.fitBounds(bounds, { padding, duration });
  }
};

export {
  areProjectsEqual,
  calculateBoundsFromGeoJSON,
  createDefaultSingleBandSymbology,
  createDefaultMultibandSymbology,
  fitMapToGeoJSON,
  getCategory,
  getDefaultStyle,
  getHillshade,
  getLocalStorageProjects,
  getMultibandMinMax,
  getSingleBandMinMax,
  getTitilerQueryParams,
  isElevationDataProduct,
  isSingleBand,
  mapApiResponseToLayers,
  setLocalStorageProjects,
};
