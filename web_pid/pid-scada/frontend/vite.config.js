import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    // Dev mode: proxy API/WS calls to the FastAPI backend
    proxy: {
      '/api':     { target: 'http://localhost:8000', changeOrigin: true },
      '/ws':      { target: 'ws://localhost:8000',   changeOrigin: true, ws: true },
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  }
})
