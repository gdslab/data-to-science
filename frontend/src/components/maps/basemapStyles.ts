import { StyleSpecification } from 'maplibre-gl';

const satelliteBasemapStyle: StyleSpecification = {
  version: 8,
  glyphs: `https://api.maptiler.com/fonts/{fontstack}/{range}.pbf?key=${
    import.meta.env.VITE_MAPTILER_API_KEY
  }`,
  sources: {
    satellite: {
      type: 'raster',
      tiles: [
        `https://api.mapbox.com/styles/v1/mapbox/satellite-streets-v12/tiles/{z}/{x}/{y}?access_token=${
          import.meta.env.VITE_MAPBOX_ACCESS_TOKEN
        }`,
      ],
      tileSize: 256,
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

export { satelliteBasemapStyle };
