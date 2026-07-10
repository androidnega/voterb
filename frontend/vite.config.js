import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

const backendTarget = process.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000'
const lanHost = process.env.LAN_HOST === '1'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: lanHost ? '0.0.0.0' : 'localhost',
    port: Number(process.env.VITE_PORT) || 5173,
    strictPort: false,
    proxy: {
      '/api': {
        target: backendTarget,
        changeOrigin: true,
      },
      '/ws': {
        target: backendTarget.replace(/^http/, 'ws'),
        ws: true,
      },
      '/media': {
        target: backendTarget,
        changeOrigin: true,
      },
    },
  },
  preview: {
    host: '0.0.0.0',
    port: Number(process.env.VITE_PORT) || 5173,
  },
})
