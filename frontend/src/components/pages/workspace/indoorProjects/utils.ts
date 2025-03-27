import chroma from 'chroma-js';

import {
  ColorMapGroupedOption,
  ColorMapOption,
} from '../../../maps/RasterSymbologySettings/cmaps';

/**
 * Returns the appropriate text color for a HSV background.
 *
 * @param {number} hue - Hue in degrees (0 to 360)
 * @param {number} saturation - Saturation in percentage (0 to 100)
 * @param {number} value - Value in percentage (0 to 100).
 * @returns {string} Tailwind class for text color.
 */
const getTextColor = (hue, saturation, value) => {
  if (!hue || !saturation || !value) return 'text-black';

  // Convert HSV to RGB
  const backgroundColor = chroma.hsv(hue, saturation / 100, value / 100);

  // Calculate contrast with white and black
  const contrastWhite = chroma.contrast(backgroundColor, 'white');
  const contrastBlack = chroma.contrast(backgroundColor, 'black');

  // Return Tailwind class based on luminance
  return contrastWhite > contrastBlack ? 'text-white' : 'text-black';
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

export {
  getTextColor,
  nivoCategoricalColors,
  nivoColorMapGroupedOptions,
  titleCaseConversion,
};
