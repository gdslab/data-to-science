import area from '@turf/area';
import { Polygon } from 'geojson';

import { GeoJSONFeature } from '../../pages/workspace/projects/Project';

export type NormalizeResult = {
  feature: GeoJSONFeature;
  pickedLargestOf?: number;
};

// Convert a (possibly MultiPolygon) feature into a single-Polygon feature.
// Trivial single-component MultiPolygons (common in shapefile-derived GeoJSON)
// are unwrapped silently. Multi-component MultiPolygons keep the largest
// component by area, with the original component count returned so callers
// can surface a notice.
export function normalizeToPolygon(feature: GeoJSONFeature): NormalizeResult {
  if (feature?.geometry?.type !== 'MultiPolygon') {
    return { feature };
  }

  const components = feature.geometry.coordinates as number[][][][];
  if (components.length === 0) {
    return { feature };
  }

  let largestIdx = 0;
  if (components.length > 1) {
    let largestArea = -Infinity;
    components.forEach((coords, idx) => {
      const polygon: Polygon = { type: 'Polygon', coordinates: coords };
      const a = area(polygon);
      if (a > largestArea) {
        largestArea = a;
        largestIdx = idx;
      }
    });
  }

  const normalized: GeoJSONFeature = {
    ...feature,
    geometry: {
      type: 'Polygon',
      coordinates: components[largestIdx],
    },
  };

  return components.length > 1
    ? { feature: normalized, pickedLargestOf: components.length }
    : { feature: normalized };
}
