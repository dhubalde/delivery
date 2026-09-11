import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vuetify from 'vite-plugin-vuetify'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue(), vuetify({ autoImport: true })],
  resolve: { alias: { '@': resolve(__dirname, 'src') } },
  server: { proxy: { '/api': 'http://localhost:8000' } },
  build: {
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router', 'pinia', '@tanstack/vue-query', 'axios'],
          vuetify: ['vuetify'],
          phone: ['libphonenumber-js'],
          admin: ['src/views/admin/AdminPlaceholder.vue'],
        },
      },
    },
  },
})
