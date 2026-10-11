const drawStyles = [
  // Yellow polygon fill (active)
  {
    id: 'gl-draw-polygon-fill-active',
    type: 'fill',
    filter: ['all', ['==', 'active', 'true'], ['==', '$type', 'Polygon']],
    paint: {
      'fill-color': '#fbb03b', // Yellow
      'fill-opacity': 0.4,
    },
  },
  // Yellow polygon fill (inactive)
  {
    id: 'gl-draw-polygon-fill-inactive',
    type: 'fill',
    filter: ['all', ['==', 'active', 'false'], ['==', '$type', 'Polygon']],
    paint: {
      'fill-color': '#fbb03b', // Yellow
      'fill-opacity': 0.4,
    },
  },
  // Dashed yellow polygon outline (active)
  {
    id: 'gl-draw-polygon-stroke-active',
    type: 'line',
    filter: ['all', ['==', 'active', 'true'], ['==', '$type', 'Polygon']],
    paint: {
      'line-color': '#fbb03b', // Yellow
      'line-width': 2,
      'line-dasharray': [2, 2], // Dashed pattern
    },
  },
  // Dashed yellow polygon outline (inactive)
  {
    id: 'gl-draw-polygon-stroke-inactive',
    type: 'line',
    filter: ['all', ['==', 'active', 'false'], ['==', '$type', 'Polygon']],
    paint: {
      'line-color': '#fbb03b', // Yellow
      'line-width': 2,
      'line-dasharray': [2, 2], // Dashed pattern
    },
  },
  // Yellow vertex points with white outline (active)
  {
    id: 'gl-draw-polygon-vertex-active',
    type: 'circle',
    filter: ['all', ['==', 'meta', 'vertex'], ['==', 'active', 'true']],
    paint: {
      'circle-radius': 4,
      'circle-color': '#fbb03b', // Yellow
      'circle-stroke-color': '#ffffff', // White
      'circle-stroke-width': 1,
    },
  },
  // Yellow vertex points with white outline (inactive)
  {
    id: 'gl-draw-polygon-vertex-inactive',
    type: 'circle',
    filter: ['all', ['==', 'meta', 'vertex'], ['==', 'active', 'false']],
    paint: {
      'circle-radius': 4,
      'circle-color': '#fbb03b', // Yellow
      'circle-stroke-color': '#ffffff', // White
      'circle-stroke-width': 1,
    },
  },
];

export { drawStyles };
