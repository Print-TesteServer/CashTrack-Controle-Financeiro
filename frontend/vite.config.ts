import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // Separa Recharts (biblioteca de gráficos - muito pesada)
          'recharts': ['recharts'],
          // Separa React Router
          'react-router': ['react-router-dom'],
          // Separa outras bibliotecas grandes
          'vendor': ['axios', 'date-fns', 'lucide-react'],
        },
      },
    },
    chunkSizeWarningLimit: 600,
  },
})


