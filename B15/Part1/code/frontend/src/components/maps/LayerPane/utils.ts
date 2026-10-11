import area from '@turf/area';
import length from '@turf/length';
import { Feature } from 'geojson';

import { Flight } from '../../pages/workspace/projects/Project';

import pointIcon from '../../../assets/point-icon.svg';
import lineIcon from '../../../assets/line-icon.svg';
import polygonIcon from '../../../assets/polygon-icon.svg';

/**
 * Returns the appropriate icon for a given geometry type.
 * @param geomType Geometry type (point, line, polygon)
 * @returns Icon path for the geometry type
 */
function getGeomTypeIcon(geomType: string): string {
  let icon = pointIcon;
  switch (geomType.toLowerCase()) {
    case 'point':
      icon = pointIcon;
      break;
    case 'line':
    case 'linestring':
      icon = lineIcon;
      break;
    case 'polygon':
      icon = polygonIcon;
      break;
  }
  return icon;
}

/**
 * Takes a date in YYYY-mm-dd format and returns it in Day, Month Date, Year format.
 * For example: 2024-03-13 to Wednesday, Mar 13, 2024
 * @param datestring Date string in YYYY-mm-dd format.
 * @returns Date string in Day, Month Date, Year format.
 */
function formatDate(datestring) {
  return new Date(datestring).toLocaleDateString('en-us', {
    timeZone: 'UTC',
    weekday: 'long',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

/**
 * Sorts flights first by date and then by id if the dates are the same.
 * @param flights Flights associated with project.
 * @returns Sorted flights by date and id.
 */
function sortedFlightsByDateAndId(flights: Flight[]): Flight[] {
  return [...flights].sort((a, b) => {
    const dateDiff =
      new Date(a.acquisition_date).getTime() -
      new Date(b.acquisition_date).getTime();
    if (dateDiff !== 0) return dateDiff;
    // For alphanumeric UUIDs, localeCompare is appropriate.
    return a.id.localeCompare(b.id);
  });
}

/**
 * Formats a polyline length as a human-readable string.
 * Returns feet for distances under 1 mile, otherwise miles.
 */
function formatLength(feature: Feature): string {
  const mi = length(feature, { units: 'miles' });
  if (mi < 1) {
    return `${(mi * 5280).toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })} ft`;
  }
  return `${mi.toFixed(1)} mi`;
}

/**
 * Formats a polygon area as a human-readable string.
 * Returns ft² for areas under 1 acre, otherwise acres.
 */
function formatArea(feature: Feature): string {
  const m2 = area(feature);
  const ft2 = m2 * 10.7639;
  const acres = ft2 / 43560;
  if (acres < 1) {
    return `${ft2.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })} ft²`;
  }
  return `${acres.toFixed(1)} ac`;
}

const NON_MAP_DATA_TYPES = ['point_cloud', 'panoramic', '3dgs'] as const;

export {
  formatArea,
  formatDate,
  formatLength,
  getGeomTypeIcon,
  NON_MAP_DATA_TYPES,
  sortedFlightsByDateAndId,
};
