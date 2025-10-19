import { LayerProps } from 'react-map-gl/maplibre';

import { MapLayerProps } from './MapLayersContext';

// Cluster layers
export const clusterLayerInner: LayerProps = {
  id: 'clusters-inner',
  type: 'circle',
  source: 'projects',
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
  source: 'projects',
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
  source: 'projects',
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

// Project vector layer
export const getProjectVectorLayer = (
  layer: MapLayerProps
): LayerProps | LayerProps[] => {
  const geomType = layer.type.toLowerCase();

  switch (geomType) {
    case 'point':
      return {
        id: layer.id,
        type: 'circle',
        source: layer.id,
        'source-layer': 'public.vector_layers',
        paint: {
          'circle-radius': 5,
          'circle-color': layer.color,
          'circle-opacity': layer.opacity / 100,
        },
      };
    case 'line':
      return {
        id: layer.id,
        type: 'line',
        source: layer.id,
        'source-layer': 'public.vector_layers',
        paint: {
          'line-color': layer.color,
          'line-opacity': layer.opacity / 100,
          'line-width': 2,
        },
      };
    case 'polygon':
      return [
        {
          id: layer.id,
          type: 'fill',
          source: layer.id,
          'source-layer': 'public.vector_layers',
          paint: {
            'fill-color': layer.fill || layer.color,
            'fill-opacity': layer.opacity / 100,
          },
        },
        {
          id: `${layer.id}-border`,
          type: 'line',
          source: layer.id,
          'source-layer': 'public.vector_layers',
          paint: {
            'line-color': layer.color,
            'line-width': 2,
          },
        },
      ];
    default:
      throw new Error(`Unexpected geometry type: ${geomType}`);
  }
};
