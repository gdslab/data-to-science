import { StyleSpecification } from 'maplibre-gl';

// Define config interface
interface MapConfig {
  osmLabelFilter?: string;
}

// Helper function to parse osmLabelFilter and create country filters for a specific scale
const createA2Filter = (
  osmLabelFilter: string | undefined,
  scale: string
): any[] => {
  if (!osmLabelFilter) {
    return []; // No additional filters if osmLabelFilter is not provided
  }

  // Parse filter string into country codes for this scale
  const filterEntries = osmLabelFilter.split(',').map((entry) => entry.trim());
  const countriesForScale = filterEntries
    .filter((entry) => entry.endsWith(`_${scale}`))
    .map((entry) => entry.replace(`_${scale}`, ''));

  if (countriesForScale.length === 0) {
    return []; // No filters for this scale
  }

  // Create filter conditions to exclude these countries
  return countriesForScale.map((countryCode) => [
    '!=',
    ['get', 'iso_a2'],
    countryCode,
  ]);
};

const getMapboxSatelliteBasemapStyle = (
  mapboxAccessToken: string
): StyleSpecification => ({
  version: 8,
  glyphs: `https://api.mapbox.com/fonts/v1/gdslab/{fontstack}/{range}.pbf?access_token=${mapboxAccessToken}`,
  sources: {
    satellite: {
      type: 'raster',
      tiles: [
        `https://api.mapbox.com/styles/v1/mapbox/satellite-streets-v12/tiles/{z}/{x}/{y}?access_token=${mapboxAccessToken}`,
      ],
      tileSize: 512,
      attribution: `© <a href="https://www.mapbox.com/about/maps/">Mapbox</a> © <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> <strong><a href="https://www.mapbox.com/map-feedback/" target="_blank">Improve this map</a></strong>`,
    },
  },
  layers: [
    {
      id: 'satellite-layer',
      type: 'raster',
      source: 'satellite',
    },
  ],
});

const osmBasemapStyle: StyleSpecification = {
  version: 8,
  glyphs: 'https://fonts.openmaptiles.org/{fontstack}/{range}.pbf',
  sources: {
    osm: {
      type: 'raster',
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    },
  },
  layers: [
    {
      id: 'osm-layer',
      type: 'raster',
      source: 'osm',
    },
  ],
};

const getWorldImageryTopoBasemapStyle = (
  maptilerApiKey?: string,
  config?: MapConfig
): StyleSpecification => {
  const baseStyle: StyleSpecification = {
    version: 8,
    glyphs: 'https://fonts.openmaptiles.org/{fontstack}/{range}.pbf',
    sources: {
      esri: {
        type: 'raster',
        tiles: [
          'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        ],
        tileSize: 256,
        maxzoom: 20,
        attribution:
          'Esri, Maxar, Earthstar Geographics, and the GIS User Community',
      },
    },
    layers: [
      {
        id: 'world-imagery-layer',
        type: 'raster',
        source: 'esri',
      },
    ],
  };

  // Only add vector labels if MapTiler API key is available
  if (maptilerApiKey) {
    baseStyle.sources['osm-labels'] = {
      type: 'vector',
      tiles: [
        `https://api.maptiler.com/tiles/v3-openmaptiles/{z}/{x}/{y}.pbf?key=${maptilerApiKey}`,
      ],
      minzoom: 0,
      maxzoom: 14,
    };

    // Continent scale labels (zoom 1-5)
    const continentFilters = createA2Filter(config?.osmLabelFilter, 'S1');
    baseStyle.layers.push({
      id: 'continent-labels',
      type: 'symbol',
      source: 'osm-labels',
      'source-layer': 'place',
      minzoom: 1,
      maxzoom: 5,
      filter: [
        'all',
        ['in', ['get', 'class'], ['literal', ['country', 'city']]],
        ...continentFilters,
      ],
      layout: {
        'text-field': ['get', 'name'],
        'text-size': [
          'case',
          ['==', ['get', 'class'], 'country'],
          18,
          ['==', ['get', 'capital'], 2],
          16,
          ['==', ['get', 'class'], 'city'],
          ['interpolate', ['linear'], ['get', 'rank'], 1, 16, 5, 12],
          14,
        ],
        'text-font': ['Open Sans Bold'],
        'text-anchor': 'center',
        'text-max-width': 8,
        'symbol-spacing': 300,
        'text-padding': 3,
      },
      paint: {
        'text-color': '#ffffff',
        'text-halo-color': '#000000',
        'text-halo-width': 1,
      },
    });

    // Regional scale labels (zoom 4-9)
    const regionalFilters = createA2Filter(config?.osmLabelFilter, 'S2');
    baseStyle.layers.push({
      id: 'regional-labels',
      type: 'symbol',
      source: 'osm-labels',
      'source-layer': 'place',
      minzoom: 4,
      maxzoom: 9,
      filter: [
        'all',
        ['in', ['get', 'class'], ['literal', ['country', 'city', 'town']]],
        ...regionalFilters,
      ],
      layout: {
        'text-field': ['get', 'name'],
        'text-size': [
          'case',
          ['==', ['get', 'class'], 'country'],
          20,
          ['==', ['get', 'capital'], 2],
          18,
          ['==', ['get', 'class'], 'city'],
          ['interpolate', ['linear'], ['get', 'rank'], 1, 18, 10, 14],
          ['==', ['get', 'class'], 'town'],
          12,
          14,
        ],
        'text-font': ['Open Sans Semibold'],
        'text-anchor': 'center',
        'text-max-width': 10,
        'symbol-spacing': 250,
        'text-padding': 2,
      },
      paint: {
        'text-color': '#ffffff',
        'text-halo-color': '#000000',
        'text-halo-width': 1,
      },
    });

    // City/local scale labels (zoom 8-13)
    const cityFilters = createA2Filter(config?.osmLabelFilter, 'S3');
    const cityLayer: any = {
      id: 'city-local-labels',
      type: 'symbol',
      source: 'osm-labels',
      'source-layer': 'place',
      minzoom: 8,
      maxzoom: 13,
      layout: {
        'text-field': ['get', 'name'],
        'text-size': [
          'case',
          ['==', ['get', 'class'], 'country'],
          22,
          ['==', ['get', 'capital'], 2],
          20,
          ['==', ['get', 'class'], 'city'],
          ['interpolate', ['linear'], ['get', 'rank'], 1, 20, 10, 16],
          ['==', ['get', 'class'], 'town'],
          14,
          ['==', ['get', 'class'], 'village'],
          12,
          14,
        ],
        'text-font': ['Open Sans Regular'],
        'text-anchor': 'center',
        'text-max-width': 12,
        'symbol-spacing': 200,
        'text-padding': 2,
      },
      paint: {
        'text-color': '#ffffff',
        'text-halo-color': '#000000',
        'text-halo-width': 1.5,
      },
    };

    // Add filter only if there are filters to apply
    if (cityFilters.length > 0) {
      cityLayer.filter = ['all', ...cityFilters];
    }

    baseStyle.layers.push(cityLayer);

    // Street level labels (zoom 13+)
    const streetFilters = createA2Filter(config?.osmLabelFilter, 'S4');
    const streetLayer: any = {
      id: 'street-level-labels',
      type: 'symbol',
      source: 'osm-labels',
      'source-layer': 'place',
      minzoom: 13,
      layout: {
        'text-field': ['get', 'name'],
        'text-size': [
          'case',
          ['==', ['get', 'class'], 'country'],
          24,
          ['==', ['get', 'capital'], 2],
          22,
          ['==', ['get', 'class'], 'city'],
          ['interpolate', ['linear'], ['get', 'rank'], 1, 22, 10, 18],
          ['==', ['get', 'class'], 'town'],
          16,
          ['==', ['get', 'class'], 'village'],
          14,
          16,
        ],
        'text-font': ['Open Sans Regular'],
        'text-anchor': 'center',
        'text-max-width': 15,
        'symbol-spacing': 150,
        'text-padding': 1,
      },
      paint: {
        'text-color': '#ffffff',
        'text-halo-color': '#000000',
        'text-halo-width': 2,
      },
    };

    // Add filter only if there are filters to apply
    if (streetFilters.length > 0) {
      streetLayer.filter = ['all', ...streetFilters];
    }

    baseStyle.layers.push(streetLayer);

    // Add road labels (street names) - zoom 12+
    const roadLabelLayer: any = {
      id: 'road-labels',
      type: 'symbol',
      source: 'osm-labels',
      'source-layer': 'transportation_name',
      minzoom: 12,
      layout: {
        'text-field': ['get', 'name'],
        'text-size': ['interpolate', ['linear'], ['zoom'], 12, 10, 18, 14],
        'text-font': ['Open Sans Regular'],
        'text-transform': 'uppercase',
        'text-letter-spacing': 0.05,
        'text-offset': [0, 1.5],
        'text-anchor': 'top',
        'symbol-placement': 'line',
        'text-max-width': 8,
      },
      paint: {
        'text-color': '#ffffff',
        'text-halo-color': '#000000',
        'text-halo-width': 1.5,
      },
    };

    // Add road network lines for better visibility - zoom 12+
    const roadNetworkLayer: any = {
      id: 'road-network',
      type: 'line',
      source: 'osm-labels',
      'source-layer': 'transportation',
      minzoom: 12,
      filter: [
        'in',
        ['get', 'class'],
        ['literal', ['street', 'primary', 'secondary', 'tertiary']],
      ],
      paint: {
        'line-color': '#ffffff',
        'line-width': ['interpolate', ['linear'], ['zoom'], 12, 0.5, 18, 2],
        'line-opacity': 0.4,
      },
    };

    baseStyle.layers.push(roadNetworkLayer);
    baseStyle.layers.push(roadLabelLayer);
  }

  return baseStyle;
};

// For backward compatibility, keep the old constant version without labels
const worldImageryTopoBasemapStyle: StyleSpecification =
  getWorldImageryTopoBasemapStyle();

export {
  getMapboxSatelliteBasemapStyle,
  osmBasemapStyle,
  worldImageryTopoBasemapStyle,
  getWorldImageryTopoBasemapStyle,
};
