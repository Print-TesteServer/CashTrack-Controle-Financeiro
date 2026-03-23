import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const proxyTarget = env.VITE_API_PROXY_TARGET || 'http://localhost:8000'

  const apiProxy = {
    '/api': {
      target: proxyTarget,
      changeOrigin: true,
    },
  }

  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: apiProxy,
    },
    // Mesmo proxy em `vite preview` (build local) — sem isso, /api não existe no servidor estático
    preview: {
      port: 4173,
      proxy: apiProxy,
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
  }
})


