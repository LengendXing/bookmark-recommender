import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        bypass: (req) => {
          const url = req.url || ''
          // Don't proxy frontend SPA routes (only proxy actual API calls)
          if (/^\/api(?!\/)/.test(url)) return url
          if (/^\/api-/.test(url)) return url
        },
      },
    },
  },
})
