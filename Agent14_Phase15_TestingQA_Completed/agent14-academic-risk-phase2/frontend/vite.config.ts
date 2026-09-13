import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const apiBaseUrl = process.env.VITE_API_BASE_URL
if (process.env.NODE_ENV === 'production' && !apiBaseUrl) {
  throw new Error('VITE_API_BASE_URL must be configured for production builds')
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
})
