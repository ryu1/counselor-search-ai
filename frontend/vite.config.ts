import vue from '@vitejs/plugin-vue'
import {defineConfig} from 'vite'
import tailwindcss from 'tailwindcss'
import {resolve} from 'path'

export default defineConfig({
  plugins: [vue()],
  css: {
    postcss: {
      plugins: [tailwindcss()],
    },
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 3000,
  },
})