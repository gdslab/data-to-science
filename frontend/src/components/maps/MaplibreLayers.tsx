import { LayerProps } from 'react-map-gl/maplibre';

import { MapLayerProps } from './MapLayersContext';

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
            'fill-color': layer.color,
            'fill-opacity': layer.opacity / 100,
          },
        },
        {
          id: `${layer.id}-border`,
          type: 'line',
          source: layer.id,
          'source-layer': 'public.vector_layers',
          paint: {
            'line-color': '#FFFFFF',
            'line-width': 2,
          },
        },
      ];
    default:
      throw new Error(`Unexpected geometry type: ${geomType}`);
  }
};
