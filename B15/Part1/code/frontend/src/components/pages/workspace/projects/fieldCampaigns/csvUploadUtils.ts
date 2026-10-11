/**
 * Compares two arrays of header names. Returns true if both arrays
 * are the same size and contain same header names in same order.
 * @param {string[]} headers1 First array of header names.
 * @param {string[]} headers2 Second array of header names.
 * @returns {boolean} True if both arrays match, false otherwise.
 */
export const headersMatch = (headers1: string[], headers2: string[]): boolean => {
  if (headers1.length !== headers2.length) return false;
  for (let i = 0; i < headers1.length; i++) {
    if (headers1[i] !== headers2[i]) return false;
  }
  return true;
};