const defaultTheme = {
  primary: '#cfb991',
  secondary: '#8e6f3e',
  info: '#daaa00',
  warning: '#ddb945',
  error: '#ebd99f',
};

const altTheme1 = {
  primary: '#1e425e',
  secondary: '#256670',
  info: '#ade28a',
  warning: '#edfa8b',
  error: '#407056',
};

const altTheme2 = {
  primary: '#3d5a80',
  secondary: '#98c1d9',
  info: '#e0fbfc',
  warning: '#ee6c4d',
  error: '#293241',
};

const altTheme3 = {
  primary: '#e6ebed',
  secondary: '#ffc100',
  info: '#1e9adf',
  warning: '#636466',
  error: '#063852',
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
