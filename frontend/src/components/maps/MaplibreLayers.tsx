import { LayerProps } from 'react-map-gl/maplibre';

// Cluster layers
export const clusterLayer: LayerProps = {
  id: 'clusters',
  type: 'circle',
  source: 'projects',
  filter: ['has', 'point_count'],
  paint: {
    'circle-color': [
      'step',
      ['get', 'point_count'],
      '#51bbd6',
      50,
      '#f1f075',
      150,
      '#f28cb1',
    ],
    'circle-radius': ['step', ['get', 'point_count'], 20, 50, 30, 150, 40],
  },
};

export const clusterCountLayer: LayerProps = {
  id: 'cluster-count',
  type: 'symbol',
  source: 'projects',
  filter: ['has', 'point_count'],
  layout: {
    'text-field': '{point_count_abbreviated}',
    'text-font': ['DIN Offc Pro Medium', 'Arial Unicode MS Bold'],
    'text-size': 12,
  },
};

export const unclusteredPointLayer: LayerProps = {
  id: 'unclustered-point',
  type: 'circle',
  source: 'earthquakes',
  filter: ['!', ['has', 'point_count']],
  paint: {
    'circle-color': '#11b4da',
    'circle-radius': 4,
    'circle-stroke-width': 1,
    'circle-stroke-color': '#fff',
  },
};

// Project boundary layer
export const projectBoundaryLayer: LayerProps = {
  id: 'project-boundary',
  type: 'line',
  source: 'project-boundary',
  layout: {},
  paint: {
    'line-color': '#fff',
  },
};
