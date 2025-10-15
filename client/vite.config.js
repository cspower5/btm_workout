import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const LIVE_API_URL = "https://btm-workout.onrender.com";

export default defineConfig(({ mode }) => ({
  plugins: [react()],
    server: {
      proxy: {
        '/api': {
          target: 'https://btm-workout.onrender.com',
          changeOrigin: true,
          secure: true,
          // Optionally rewrite: remove /api prefix if needed
          // rewrite: (path) => path.replace(/^\/api/, '/api'),
        },
      },
    },
  base: mode === 'production' ? '/btm_workout/' : '/',
  define: {
    'import.meta.env.VITE_API_URL': JSON.stringify(LIVE_API_URL)
  }
}));
