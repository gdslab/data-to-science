import { StyleSpecification } from 'maplibre-gl';

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
  maptilerApiKey?: string
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
    baseStyle.layers.push({
      id: 'continent-labels',
      type: 'symbol',
      source: 'osm-labels',
      'source-layer': 'place',
      minzoom: 1,
      maxzoom: 5,
      filter: ['in', ['get', 'class'], ['literal', ['country', 'city']]],
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
        'text-font': ['Open Sans Regular'],
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
    baseStyle.layers.push({
      id: 'regional-labels',
      type: 'symbol',
      source: 'osm-labels',
      'source-layer': 'place',
      minzoom: 4,
      maxzoom: 9,
      filter: [
        'in',
        ['get', 'class'],
        ['literal', ['country', 'city', 'town']],
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
        'text-font': ['Open Sans Regular'],
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
    baseStyle.layers.push({
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
        'text-font': ['Open Sans Semibold'],
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
    });

    // Street level labels (zoom 13+)
    baseStyle.layers.push({
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
        'text-font': ['Open Sans Bold'],
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
    });
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
