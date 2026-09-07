/**
 * Tailwind CSS configuration for Counselor Search AI Demo
 */

/** @type {import('tailwindcss').Config} */
const config = {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        serif: ['Georgia', 'serif'],
      },
      colors: {
        counselor: {
          primary: '#1a1a2e',
          secondary: '#16213e',
          accent: '#e94560',
          success: '#06d6a0',
          info: '#0284c7',
          warning: '#f6ad55',
        }
      },
    },
  },
  plugins: [],
}

export default config