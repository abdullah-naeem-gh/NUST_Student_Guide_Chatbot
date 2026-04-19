/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        charcoal: {
          DEFAULT: '#2D3E50',
          light:   '#364a5e',
          dark:    '#243343',
          darker:  '#1c2a38',
        },
        surface:  '#364a5e',
        platinum: '#F4F8F9',
      },
      fontFamily: {
        sans: ['Lora', 'Georgia', 'Times New Roman', 'serif'],
        serif: ['Lora', 'Georgia', 'Times New Roman', 'serif'],
        mono: ['IBM Plex Mono', 'ui-monospace', 'monospace'],
      },
      borderColor: {
        subtle: 'rgba(255, 255, 255, 0.08)',
      },
    },
  },
  plugins: [],
}
