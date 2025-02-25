import { Flight } from '../../pages/workspace/projects/Project';

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

export { formatDate, sortedFlightsByDateAndId };
