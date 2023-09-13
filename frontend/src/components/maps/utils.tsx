import chroma, { Color, Scale } from 'chroma-js';

import { Band } from '../pages/projects/ProjectDetail';

function getColorScale(colorRamp: string): string | Color {
  switch (colorRamp) {
    case 'spectral':
      return 'Spectral';
    case 'rdylbu':
      return 'RdYlBu';
    case 'ylgn':
      return 'YlGn';
    default:
      return 'Spectral';
  }
}

export function setPixelColors(values: number[], bandInfo: Band[], colorRamp: string) {
  // Check if the pixel should be colored, if not make it transparent
  if (!hasDataForAllBands(values)) {
    return '#00000000';
  }

  // destructure the bands
  let color: Color | Scale<Color> | null = null;

  if (bandInfo.length === 1) {
    const scale = chroma
      .scale(getColorScale(colorRamp))
      .domain([bandInfo[0].stats.minimum, bandInfo[0].stats.maximum]);
    if (
      values[0] >= bandInfo[0].stats.minimum &&
      values[0] <= bandInfo[0].stats.maximum
    ) {
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
