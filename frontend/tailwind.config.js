/** @type {import('tailwindcss').Config} */
import { loadTheme } from './themes';
import colors from 'tailwindcss/colors';

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        ...loadTheme('alt3'),
      },
    },
  },
  plugins: [],
};
