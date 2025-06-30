import { LayerProps } from 'react-map-gl/maplibre';

// Cluster layers
export const clusterLayerInner: LayerProps = {
  id: 'clusters-inner',
  type: 'circle',
  source: 'iforester-source',
  filter: ['has', 'point_count'],
  paint: {
    'circle-color': [
      'step',
      ['get', 'point_count'],
      '#51bbd6',
      25,
      '#f1f075',
      50,
      '#f28cb1',
    ],
    'circle-radius': ['step', ['get', 'point_count'], 15, 25, 20, 50, 30],
  },
};

export const clusterLayerOuter: LayerProps = {
  id: 'clusters-outer',
  type: 'circle',
  source: 'iforester-source',
  filter: ['has', 'point_count'],
  paint: {
    'circle-color': [
      'step',
      ['get', 'point_count'],
      '#51bbd6',
      25,
      '#f1f075',
      50,
      '#f28cb1',
    ],
    'circle-radius': ['step', ['get', 'point_count'], 20, 25, 30, 50, 40],
    'circle-opacity': 0.75,
  },
};

export const clusterCountLayer: LayerProps = {
  id: 'cluster-count',
  type: 'symbol',
  source: 'iforester-source',
  filter: ['has', 'point_count'],
  layout: {
    'text-field': '{point_count_abbreviated}',
    'text-font': ['Open Sans Semibold'],
    'text-size': ['step', ['get', 'point_count'], 12, 25, 16, 50, 22],
  },
  paint: {
    'text-color': '#000000',
    'text-halo-color': '#ffffff',
    'text-halo-width': 1,
    'text-halo-blur': 0.5,
  },
};

export const getUnclusteredPointLayer = (activeLayer: string): LayerProps => {
  return {
    id: 'unclustered-point',
    type: 'circle',
    source: 'iforester-source',
    filter: ['all', ['!', ['has', 'point_count']]],
    paint: {
      'circle-color': [
        'case',
        ['==', ['get', 'id'], activeLayer],
        '#ffff00',
        '#fff',
      ],
      'circle-radius': ['case', ['==', ['get', 'id'], activeLayer], 8, 4],
      'circle-stroke-width': 1,
      'circle-stroke-color': '#000',
    },
  };
};
