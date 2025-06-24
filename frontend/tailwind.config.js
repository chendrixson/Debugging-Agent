/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'console-bg': '#1a1a1a',
        'console-text': '#00ff00',
        'console-error': '#ff0000',
        'console-input': '#ffff00',
        'console-system': '#00ffff',
        'console-state': '#ff00ff',
        'console-breakpoint': '#ff8800',
        'console-exception': '#ff0088',
        'console-terminated': '#880000',
      },
      fontFamily: {
        'mono': ['Courier New', 'monospace'],
      },
    },
  },
  plugins: [],
} 