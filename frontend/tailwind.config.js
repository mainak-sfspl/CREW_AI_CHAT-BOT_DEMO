/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'sampurna-dark': '#0f172a',
        'sampurna-card': '#1e293b',
      },
    },
  },
  plugins: [],
}
