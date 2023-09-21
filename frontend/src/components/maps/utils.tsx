import chroma, { Color, Scale } from 'chroma-js';

import { Band } from '../pages/projects/ProjectDetail';
import { SymbologySettings } from './MapContext';

function getColorScale(colorRamp: string): string | Color {
  switch (colorRamp) {
    case 'bupu':
      return 'BuPu';
    case 'spectral':
      return 'Spectral';
    case 'turbo':
      // @ts-ignore
      return ['#30123b', '#7a0403'];
    case 'ylgnbu':
      return 'YlGnBu';
    case 'ylorrd':
      return 'YlOrRd';
    default:
      return 'Spectral';
  }
}

export function setPixelColors(
  values: number[],
  bandInfo: Band[],
  symbologySettings: SymbologySettings
) {
  // Check if the pixel should be colored, if not make it transparent
  if (!hasDataForAllBands(values)) {
    return '#00000000';
  }

  // destructure the bands
  let color: Color | Scale<Color> | null = null;

  if (bandInfo.length === 1) {
    const mean = bandInfo[0].stats.mean;
    const stddev = bandInfo[0].stats.stddev;
    const stats = {
      min:
        symbologySettings.minMax === 'userDefined'
          ? symbologySettings.userMin
          : symbologySettings.minMax === 'meanStdDev'
          ? mean - stddev * symbologySettings.meanStdDev
          : symbologySettings.min,
      max:
        symbologySettings.minMax === 'userDefined'
          ? symbologySettings.userMax
          : symbologySettings.minMax === 'meanStdDev'
          ? mean + stddev * symbologySettings.meanStdDev
          : symbologySettings.max,
    };

    const scale = chroma
      .scale(getColorScale(symbologySettings.colorRamp))
      .domain([stats.min, stats.max]);

    if (values[0] >= stats.min && values[0] <= stats.max) {
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
