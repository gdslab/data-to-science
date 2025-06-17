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

const worldImageryTopoBasemapStyle: StyleSpecification = {
  version: 8,
  glyphs: 'https://fonts.openmaptiles.org/{fontstack}/{range}.pbf',
  sources: {
    esri: {
      type: 'raster',
      tiles: [
        'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      ],
      tileSize: 256,
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

export {
  getMapboxSatelliteBasemapStyle,
  osmBasemapStyle,
  worldImageryTopoBasemapStyle,
};
