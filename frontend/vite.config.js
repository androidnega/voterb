import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import basicSsl from '@vitejs/plugin-basic-ssl'
import { fileURLToPath, URL } from 'node:url'

const backendTarget = process.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000'
const lanHost = process.env.LAN_HOST === '1'
// HTTPS only when explicitly requested. LAN defaults to plain HTTP.
const useHttps = process.env.VITE_HTTPS === '1'

export default defineConfig({
  plugins: [vue(), ...(useHttps ? [basicSsl()] : [])],
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
        secure: false,
      },
      '/ws': {
        target: backendTarget.replace(/^http/, 'ws'),
        ws: true,
        secure: false,
      },
      '/media': {
        target: backendTarget,
        changeOrigin: true,
        secure: false,
      },
    },
  },
    preview: {
    host: '0.0.0.0',
    port: Number(process.env.VITE_PORT) || 5173,
    proxy: {
      '/api': {
        target: backendTarget,
        changeOrigin: true,
        secure: false,
      },
      '/ws': {
        target: backendTarget.replace(/^http/, 'ws'),
        ws: true,
        secure: false,
      },
      '/media': {
        target: backendTarget,
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
