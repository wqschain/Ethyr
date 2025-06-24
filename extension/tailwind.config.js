/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Manrope', 'system-ui', 'sans-serif'],
      },
      width: {
        'popup': '350px',
      },
      colors: {
        'safe': '#10B981',
        'moderate': '#F59E0B',
        'high-risk': '#EF4444',
      }
    },
  },
  plugins: [],
} 