/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f2f6ff',
          100: '#d8e4ff',
          200: '#aac2ff',
          300: '#7ca0ff',
          400: '#4d7eff',
          500: '#255bff',
          600: '#1b45db',
          700: '#1434af',
          800: '#0d2383',
          900: '#08155c',
        },
      },
    },
  },
  plugins: [],
}

