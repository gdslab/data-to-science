/** @type {import('tailwindcss').Config} */

import { loadTheme } from './themes';

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    colors: {
      ...loadTheme('default'),
    },
    extend: {},
  },
  plugins: [],
};
