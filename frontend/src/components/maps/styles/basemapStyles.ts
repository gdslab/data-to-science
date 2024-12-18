import { StyleSpecification } from 'maplibre-gl';

const mapboxSatelliteBasemapStyle: StyleSpecification = {
  version: 8,
  glyphs: `https://api.mapbox.com/fonts/v1/gdslab/{fontstack}/{range}.pbf?access_token=${
    import.meta.env.VITE_MAPBOX_ACCESS_TOKEN
  }`,
  sources: {
    satellite: {
      type: 'raster',
      tiles: [
        `https://api.mapbox.com/styles/v1/mapbox/satellite-streets-v12/tiles/{z}/{x}/{y}?access_token=${
          import.meta.env.VITE_MAPBOX_ACCESS_TOKEN
        }`,
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
};

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

const usgsImageryTopoBasemapStyle: StyleSpecification = {
  version: 8,
  glyphs: 'https://fonts.openmaptiles.org/{fontstack}/{range}.pbf',
  sources: {
    usgs: {
      type: 'raster',
      tiles: [
        'https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryTopo/MapServer/tile/{z}/{y}/{x}',
      ],
      tileSize: 256,
      attribution:
        'USGS The National Map: Orthoimagery and US Topo. Data refreshed October, 2024.',
    },
  },
  layers: [
    {
      id: 'usgs-layer',
      type: 'raster',
      source: 'usgs',
    },
  ],
};

export { mapboxSatelliteBasemapStyle, osmBasemapStyle, usgsImageryTopoBasemapStyle };
