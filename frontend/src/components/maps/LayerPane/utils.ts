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

export { formatDate };
