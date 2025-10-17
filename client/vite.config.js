// client/vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // This will catch the '/api' from your .env.development
      '/api': {
        target: 'http://localhost:5000', // Your local Flask backend
        changeOrigin: true,
        secure: false,
        // Rewrite the path: remove '/api' so the backend gets the correct endpoint
        // e.g., /api/v1/exercises_list becomes /v1/exercises_list
        // rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  // ... other config
});

//the code below is old and replaced by the above.
// import { defineConfig } from 'vite'
// import react from '@vitejs/plugin-react'

// const LIVE_API_URL = "https://btm-workout.onrender.com";

// export default defineConfig(({ mode }) => ({
//   plugins: [react()],
//     server: {
//       proxy: {
//         '/api': {
//           target: 'https://btm-workout.onrender.com',
//           changeOrigin: true,
//           secure: true,
//           // Optionally rewrite: remove /api prefix if needed
//           // rewrite: (path) => path.replace(/^\/api/, '/api'),
//         },
//       },
//     },
//   base: mode === 'production' ? '/btm_workout/' : '/',
//   define: {
//     'import.meta.env.VITE_API_URL': JSON.stringify(LIVE_API_URL)
//   }
// }));
