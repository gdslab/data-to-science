import {
  ColorMapGroupedOption,
  ColorMapOption,
} from '../../../maps/RasterSymbologySettings/cmaps';

/**
 * Returns appropriate text color for a HSV background.
 *
 * @param {number} hue - Hue in degrees (0 to 360)
 * @param {number} saturation - Saturation in percentage (0 to 100)
 * @param {number} value - Value in percentage (0 to 100)
 * @returns {string} HEX color string in the format "#RRGGBB"
 */
const getTextColor = (hue, saturation, value) => {
  if (!hue || !saturation || !value) return 'text-black';

  const { r, g, b } = hsvToRgb(hue, saturation, value);

  // Calculate luminance (per WCAG)
  const luminance =
    0.2126 * (r / 255) + 0.7152 * (g / 255) + 0.0722 * (b / 255);

  // Return Tailwind class based on luminance
  return luminance > 0.5 ? 'text-black' : 'text-white';
};

/**
 * Converts an HSV color value to an RGB object.
 *
 * @param {number} hue - Hue in degrees (0 to 360)
 * @param {number} saturation - Saturation in percentage (0 to 100)
 * @param {number} value - Value in percentage (0 to 100)
 * @returns {{r: number, g: number, b: number}} An object with the red, green, and blue values (0–255)
 */
function hsvToRgb(hue, saturation, value) {
  // Convert saturation and value from percentage to a fraction (0–1) if necessary
  let s = saturation > 1 ? saturation / 100 : saturation;
  let v = value > 1 ? value / 100 : value;

  // Calculate Chroma
  const c = v * s;

  // Normalize hue to a value between 0 and 6
  const hh = hue / 60;

  // Calculate the intermediate value X
  const x = c * (1 - Math.abs((hh % 2) - 1));

  // Determine the temporary RGB values based on the hue segment
  let r1 = 0,
    g1 = 0,
    b1 = 0;
  if (hh >= 0 && hh < 1) {
    r1 = c;
    g1 = x;
    b1 = 0;
  } else if (hh >= 1 && hh < 2) {
    r1 = x;
    g1 = c;
    b1 = 0;
  } else if (hh >= 2 && hh < 3) {
    r1 = 0;
    g1 = c;
    b1 = x;
  } else if (hh >= 3 && hh < 4) {
    r1 = 0;
    g1 = x;
    b1 = c;
  } else if (hh >= 4 && hh < 5) {
    r1 = x;
    g1 = 0;
    b1 = c;
  } else if (hh >= 5 && hh < 6) {
    r1 = c;
    g1 = 0;
    b1 = x;
  }

  // Add the lightness adjustment (m)
  const m = v - c;
  const r = Math.round((r1 + m) * 255);
  const g = Math.round((g1 + m) * 255);
  const b = Math.round((b1 + m) * 255);

  return { r, g, b };
}

/**
 * Converts an HSV color value to a HEX string.
 *
 * @param {number} hue - Hue in degrees (0 to 360)
 * @param {number} saturation - Saturation in percentage (0 to 100)
 * @param {number} value - Value in percentage (0 to 100)
 * @returns {string} HEX color string in the format "#RRGGBB"
 */
function hsvToHex(hue, saturation, value) {
  if (!hue || !saturation || !value) return '#fff';

  const { r, g, b } = hsvToRgb(hue, saturation, value);

  // Convert each color component to a two-digit hexadecimal string
  const hexR = r.toString(16).padStart(2, '0');
  const hexG = g.toString(16).padStart(2, '0');
  const hexB = b.toString(16).padStart(2, '0');

  return `#${hexR}${hexG}${hexB}`;
}

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

export {
  hsvToHex,
  getTextColor,
  nivoCategoricalColors,
  nivoColorMapGroupedOptions,
};
