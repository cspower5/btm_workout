import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Example: https://btm-workout-api-12345.onrender.com
const LIVE_API_URL = "https://btm-workout.onrender.com"; 

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  
  // Ensures assets load correctly from the GitHub Pages subdirectory
  base: "/btm_workout/", 

  // FIX: Forces the VITE_API_URL to be defined in the production bundle
  define: {
    'import.meta.env.VITE_API_URL': JSON.stringify(LIVE_API_URL)
  }
})
