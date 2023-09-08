import chroma, { Color, Scale } from 'chroma-js';

export function setPixelColors(values: number[]) {
  // Check if the pixel should be colored, if not make it transparent
  if (!hasDataForAllBands(values)) {
    return '#00000000';
  }

  // destructure the bands
  let color: Color | Scale<Color> | null = null;
  if (values.length === 1) {
    if (values[0] >= 0) {
      const scale = chroma.scale(['yellow', '008ae5']).domain([180, 190]);
      color = scale(values[0]);
    } else {
      color = chroma('black').alpha(0.0);
    }
  } else {
    const [red, green, blue] = values;
    color = chroma(red, green, blue);
  }

  return color;
}

const hasDataForAllBands = (values: (number | boolean)[]) =>
  values.every(
    (value) => value != false || (typeof value !== 'boolean' && isNaN(value))
  );
