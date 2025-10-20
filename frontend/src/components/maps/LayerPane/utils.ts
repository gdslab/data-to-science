import { Flight } from '../../pages/projects/Project';

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

export { formatDate, getGeomTypeIcon, sortedFlightsByDateAndId };
