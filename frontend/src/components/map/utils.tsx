import chroma from 'chroma-js';

export function setPixelColors(values: number[]) {
  // Check if the pixel should be colored, if not make it transparent
  if (!hasDataForAllBands(values)) {
    return '#00000000';
  }

  // destructure the bands
  const [red, green, blue] = values;
  const color = chroma(red, green, blue);

  return color;
}

const hasDataForAllBands = (values: (number | boolean)[]) =>
  values.every(
    (value) => value != false || (typeof value !== 'boolean' && isNaN(value))
  );
