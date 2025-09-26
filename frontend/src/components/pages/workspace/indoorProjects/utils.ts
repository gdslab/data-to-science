import chroma from 'chroma-js';

import {
  ColorMapGroupedOption,
  ColorMapOption,
} from '../../../maps/RasterSymbologySettings/cmaps';
import { IndoorProjectDataVizRecord } from './IndoorProject';

/**
 * Returns the appropriate text color for a HSV background.
 *
 * @param {number} hue - Hue in degrees (0 to 360)
 * @param {number} saturation - Saturation in percentage (0 to 100)
 * @param {number} value - Value in percentage (0 to 100).
 * @returns {string} Tailwind class for text color.
 */
const getTextColor = (hue, saturation, value) => {
  console.log('hue, saturation, value', hue, saturation, value);
  if (!hue || !saturation || !value) return 'text-black';

  // Convert HSV to RGB
  const backgroundColor = chroma.hsv(hue, saturation / 100, value / 100);

  // Calculate contrast with white and black
  const contrastWhite = chroma.contrast(backgroundColor, 'white');
  const contrastBlack = chroma.contrast(backgroundColor, 'black');
  console.log('contrastWhite', contrastWhite);
  console.log('contrastBlack', contrastBlack);
  // Return Tailwind class based on luminance
  return contrastWhite > contrastBlack ? 'text-white' : 'text-black';
};

/**
 * Stretches the values of an array to a new range.
 *
 * @param {number[]} values - The array of values to stretch.
 * @param {number} outMin - The minimum value of the new range.
 * @param {number} outMax - The maximum value of the new range.
 * @returns {number[]} The stretched values.
 */
const stretch = (
  values: number[],
  outMin: number = 0.5,
  outMax: number = 1.0
): number[] => {
  const inMin = Math.min(...values);
  const inMax = Math.max(...values);
  return values.map((v) => {
    const t = (v - inMin) / (inMax - inMin || 1);
    return outMin + t * (outMax - outMin);
  });
};

/**
 * Normalizes the values of an array to a new range.
 *
 * @param {number[]} values - The array of values to normalize.
 * @returns {number[]} The normalized values.
 */
const getNormalizedValues = (values: number[]): number[] => {
  return values.map((value) => (value != null ? value / 100 : 0));
};

/**
 * Returns the normalized and stretched values of an array.
 *
 * @param {IndoorProjectDataVizRecord[][]} data - The data to normalize and stretch.
 * @returns {Object} An object containing the stretched saturation and intensity values.
 */
const getNormalizedAndStretchedValues = (
  data: IndoorProjectDataVizRecord[][]
): { stretchedSValues: number[]; stretchedVValues: number[] } => {
  const sValues = getNormalizedValues(data.map((g) => g?.[0]?.saturation ?? 0));
  const vValues = getNormalizedValues(data.map((g) => g?.[0]?.intensity ?? 0));

  const stretchedSValues = stretch(sValues, 0.5, 1.0);
  const stretchedVValues = stretch(vValues, 0.5, 1.0);

  return { stretchedSValues, stretchedVValues };
};

const nivoCategoricalColors: readonly ColorMapOption[] = [
  { value: 'nivo', label: 'Nivo' },
  { value: 'category10', label: 'Category 10' },
  { value: 'accent', label: 'Accent' },
  { value: 'dark2', label: 'Dark 2' },
  { value: 'paired', label: 'Paired' },
  { value: 'pastel1', label: 'Pastel 1' },
  { value: 'pastel2', label: 'Pastel 2' },
  { value: 'set1', label: 'Set 1' },
  { value: 'set2', label: 'Set 2' },
  { value: 'set3', label: 'Set 3' },
  { value: 'tableau10', label: 'Tableau 10' },
];

const nivoDivergingColors: readonly ColorMapOption[] = [
  { value: 'brown_blueGreen', label: 'Brown → Blue Green' },
  { value: 'purpleRed_green', label: 'Purple Red → Green' },
  { value: 'pink_yellowGreen', label: 'Pink → Yellow Green' },
  { value: 'purple_orange', label: 'Purple → Orange' },
  { value: 'red_blue', label: 'Red → Blue' },
  { value: 'red_grey', label: 'Red → Grey' },
  { value: 'red_yellow_blue', label: 'Red → Yellow → Blue' },
  { value: 'red_yellow_green', label: 'Red → Yellow → Green' },
  { value: 'spectral', label: 'Spectral' },
];

const nivoSequentialColors: readonly ColorMapOption[] = [
  { value: 'blues', label: 'Blues' },
  { value: 'greens', label: 'Greens' },
  { value: 'greys', label: 'Greys' },
  { value: 'oranges', label: 'Oranges' },
  { value: 'purples', label: 'Purples' },
  { value: 'reds', label: 'Reds' },
  { value: 'blue_green', label: 'Blue → Green' },
  { value: 'blue_purple', label: 'Blue → Purple' },
  { value: 'green_blue', label: 'Green → Blue' },
  { value: 'orange_red', label: 'Orange → Red' },
  { value: 'purple_blue_green', label: 'Purple → Blue → Green' },
  { value: 'purple_blue', label: 'Purple → Blue' },
  { value: 'purple_red', label: 'Purple → Red' },
  { value: 'red_purple', label: 'Red → Purple' },
  { value: 'yellow_green_blue', label: 'Yellow → Green → Blue' },
  { value: 'yellow_green', label: 'Yellow → Green' },
  { value: 'yellow_orange_brown', label: 'Yellow → Orange → Brown' },
  { value: 'yellow_orange_red', label: 'Yellow → Orange → Red' },
];

const nivoColorMapGroupedOptions: readonly ColorMapGroupedOption[] = [
  {
    label: 'Categorical Colors',
    options: nivoCategoricalColors,
  },
  {
    label: 'Diverging Colors',
    options: nivoDivergingColors,
  },
  {
    label: 'Sequential Colors',
    options: nivoSequentialColors,
  },
];

/**
 * Converts a string to title case.
 *
 * @param {string} str - The string to convert.
 * @returns {string} The title case string.
 */
const titleCaseConversion = (str: string): string => {
  return str.slice(0, 1).toUpperCase() + str.slice(1, str.length);
};

/**
 * Triggers a client-side CSV download given headers and rows.
 */
const downloadCSV = (
  filename: string,
  headers: Array<string | number>,
  rows: Array<Array<unknown>>
): void => {
  const escapeCell = (value: unknown): string => {
    if (value === null || value === undefined) return '';
    const str = String(value);
    const escaped = str.replace(/"/g, '""');
    const needsQuotes = /[",\n]/.test(escaped);
    return needsQuotes ? `"${escaped}"` : escaped;
  };

  const csv = [headers, ...rows]
    .map((row) => row.map(escapeCell).join(','))
    .join('\n');

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

export {
  getNormalizedAndStretchedValues,
  getTextColor,
  nivoCategoricalColors,
  nivoColorMapGroupedOptions,
  nivoSequentialColors,
  titleCaseConversion,
  downloadCSV,
};
