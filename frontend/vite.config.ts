import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vuetify from 'vite-plugin-vuetify'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue(), vuetify({ autoImport: true })],
  resolve: { alias: { '@': resolve(__dirname, 'src') } },
  server: { proxy: { '/api': 'http://localhost:8000' } },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          admin: ['src/views/admin/AdminPlaceholder.vue'],
        },
      },
    },
  },
})
