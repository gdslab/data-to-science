const defaultTheme = {
  primary: '#cfb991',
  secondary: '#8e6f3e',
  accent1: '#daaa00',
  accent2: '#ddb945',
  accent3: '#ebd99f',
  'accent3-dark': '#bcad7f',
};

const altTheme1 = {
  primary: '#1e425e',
  secondary: '#256670',
  accent1: '#ade28a',
  accent2: '#edfa8b',
  accent3: '#407056',
  'accent3-dark': '#335944',
};

const altTheme2 = {
  primary: '#3d5a80',
  secondary: '#98c1d9',
  accent1: '#e0fbfc',
  accent2: '#ee6c4d',
  accent3: '#293241',
  'accent3-dark': '#202834',
};

const altTheme3 = {
  primary: '#e6ebed',
  secondary: '#ffc100',
  accent1: '#237be6',
  accent2: '#636466',
  accent3: '#003169',
  'accent3-dark': '#002754',
};

export function loadTheme(themeName) {
  switch (themeName) {
    case 'default':
      return defaultTheme;
    case 'alt1':
      return altTheme1;
    case 'alt2':
      return altTheme2;
    case 'alt3':
      return altTheme3;
    default:
      return defaultTheme;
  }
}
