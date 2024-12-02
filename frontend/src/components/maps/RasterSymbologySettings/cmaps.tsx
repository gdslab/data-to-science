type CMaps = [string, string[]][];

export interface ColorMapOption {
  readonly value: string;
  readonly label: string;
}

export const uniformSequentialOptions: readonly ColorMapOption[] = [
  { value: 'viridis', label: 'viridis' },
  { value: 'plasma', label: 'plasma' },
  { value: 'inferno', label: 'inferno' },
  { value: 'magma', label: 'magma' },
  { value: 'cividis', label: 'cividis' },
];

export const sequentialOptions: readonly ColorMapOption[] = [
  { value: 'purples', label: 'purples' },
  { value: 'blues', label: 'blues' },
  { value: 'greens', label: 'greens' },
  { value: 'oranges', label: 'oranges' },
  { value: 'reds', label: 'reds' },
  { value: 'ylorbr', label: 'ylorbr' },
  { value: 'ylorrd', label: 'ylorrd' },
  { value: 'orrd', label: 'orrd' },
  { value: 'purd', label: 'purd' },
  { value: 'rdpu', label: 'rdpu' },
  { value: 'bupu', label: 'bupu' },
  { value: 'gnbu', label: 'gnbu' },
  { value: 'pubu', label: 'pubu' },
  { value: 'ylgnbu', label: 'ylgnbu' },
  { value: 'pubugn', label: 'pubugn' },
  { value: 'bugn', label: 'bugn' },
  { value: 'ylgn', label: 'ylgn' },
];

export const sequential2Options: readonly ColorMapOption[] = [
  { value: 'binary', label: 'binary' },
  { value: 'gist_yarg', label: 'gist_yarg' },
  { value: 'gist_gray', label: 'gist_gray' },
  { value: 'gray', label: 'gray' },
  { value: 'bone', label: 'bone' },
  { value: 'pink', label: 'pink' },
  { value: 'spring', label: 'spring' },
  { value: 'summer', label: 'summer' },
  { value: 'autumn', label: 'autumn' },
  { value: 'winter', label: 'winter' },
  { value: 'cool', label: 'cool' },
  { value: 'wistia', label: 'wistia' },
  { value: 'hot', label: 'hot' },
  { value: 'afmhot', label: 'afmhot' },
  { value: 'gist_heat', label: 'gist_heat' },
  { value: 'copper', label: 'copper' },
];

export const divergingOptions: readonly ColorMapOption[] = [
  { value: 'piyg', label: 'piyg' },
  { value: 'prgn', label: 'prgn' },
  { value: 'brbg', label: 'brbg' },
  { value: 'puor', label: 'puor' },
  { value: 'rdgy', label: 'rdgy' },
  { value: 'rdbu', label: 'rdbu' },
  { value: 'rdylbu', label: 'rdylbu' },
  { value: 'rdylgn', label: 'rdylgn' },
  { value: 'spectral', label: 'spectral' },
  { value: 'coolwarm', label: 'coolwarm' },
  { value: 'bwr', label: 'bwr' },
  { value: 'seismic', label: 'seismic' },
];

export const cyclicOptions: readonly ColorMapOption[] = [
  { value: 'twilight', label: 'twilight' },
  { value: 'twilight_shifted', label: 'twilight_shifted' },
  { value: 'hsv', label: 'hsv' },
];

export const miscOptions: readonly ColorMapOption[] = [
  { value: 'flag', label: 'flag' },
  { value: 'prism', label: 'prism' },
  { value: 'ocean', label: 'ocean' },
  { value: 'gist_earth', label: 'gist_earth' },
  { value: 'terrain', label: 'terrain' },
  { value: 'gist_stern', label: 'gist_stern' },
  { value: 'gnuplot', label: 'gnuplot' },
  { value: 'gnuplot2', label: 'gnuplot2' },
  { value: 'cmrmap', label: 'cmrmap' },
  { value: 'cubehelix', label: 'cubehelix' },
  { value: 'brg', label: 'brg' },
  { value: 'gist_rainbow', label: 'gist_rainbow' },
  { value: 'rainbow', label: 'rainbow' },
  { value: 'jet', label: 'jet' },
  { value: 'nipy_spectral', label: 'nipy_spectral' },
  { value: 'gist_ncar', label: 'gist_ncar' },
];

export const qualitativeOptions: readonly ColorMapOption[] = [
  { value: 'pastel1', label: 'pastel1' },
  { value: 'pastel2', label: 'pastel2' },
  { value: 'paired', label: 'paired' },
  { value: 'accent', label: 'accent' },
  { value: 'dark2', label: 'dark2' },
  { value: 'set1', label: 'set1' },
  { value: 'set2', label: 'set2' },
  { value: 'set3', label: 'set3' },
  { value: 'tab10', label: 'tab10' },
  { value: 'tab20', label: 'tab20' },
  { value: 'tab20b', label: 'tab20b' },
  { value: 'tab20c', label: 'tab20c' },
];

interface ColorMapGroupedOption {
  readonly label: string;
  readonly options: readonly ColorMapOption[];
}

export const colorMapGroupedOptions: readonly ColorMapGroupedOption[] = [
  {
    label: 'Perceptually Uniform Sequential',
    options: uniformSequentialOptions,
  },
  {
    label: 'Sequential',
    options: sequentialOptions,
  },
  {
    label: 'Sequential [2]',
    options: sequential2Options,
  },
  {
    label: 'Diverging',
    options: divergingOptions,
  },
  {
    label: 'Cyclic',
    options: cyclicOptions,
  },
  {
    label: 'Miscellaneous',
    options: miscOptions,
  },
  {
    label: 'Qualitative',
    options: qualitativeOptions,
  },
];

export const cmaps: CMaps = [
  [
    'Perceptually Uniform Sequential',
    ['viridis', 'plasma', 'inferno', 'magma', 'cividis'],
  ],
  [
    'Sequential',
    [
      'purples',
      'blues',
      'greens',
      'oranges',
      'reds',
      'ylorbr',
      'ylorrd',
      'orrd',
      'purd',
      'rdpu',
      'bupu',
      'gnbu',
      'pubu',
      'ylgnbu',
      'pubugn',
      'bugn',
      'ylgn',
    ],
  ],
  [
    'Sequential [2]',
    [
      'binary',
      'gist_yarg',
      'gist_gray',
      'gray',
      'bone',
      'pink',
      'spring',
      'summer',
      'autumn',
      'winter',
      'cool',
      'wistia',
      'hot',
      'afmhot',
      'gist_heat',
      'copper',
    ],
  ],
  [
    'Diverging',
    [
      'piyg',
      'prgn',
      'brbg',
      'puor',
      'rdgy',
      'rdbu',
      'rdylbu',
      'rdylgn',
      'spectral',
      'coolwarm',
      'bwr',
      'seismic',
    ],
  ],
  ['Cyclic', ['twilight', 'twilight_shifted', 'hsv']],
  [
    'Miscellaneous',
    [
      'flag',
      'prism',
      'ocean',
      'gist_earth',
      'terrain',
      'gist_stern',
      'gnuplot',
      'gnuplot2',
      'cmrmap',
      'cubehelix',
      'brg',
      'gist_rainbow',
      'rainbow',
      'jet',
      'nipy_spectral',
      'gist_ncar',
    ],
  ],
  [
    'Qualitative colormaps',
    [
      'pastel1',
      'pastel2',
      'paired',
      'accent',
      'dark2',
      'set1',
      'set2',
      'set3',
      'tab10',
      'tab20',
      'tab20b',
      'tab20c',
    ],
  ],
];
