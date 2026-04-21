import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vue-vendor': ['vue', 'vue-router'],
          'primevue-core': [
            'primevue/button',
            'primevue/card',
            'primevue/config',
            'primevue/inputtext',
            'primevue/message',
            'primevue/select',
            'primevue/skeleton',
            'primevue/tag',
          ],
          'primevue-data': [
            'primevue/column',
            'primevue/datatable',
            'primevue/paginator',
          ],
        },
      },
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
  },
})
