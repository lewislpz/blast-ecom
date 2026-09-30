import react from '@vitejs/plugin-react'
import { configDefaults, defineConfig } from 'vitest/config'

const apiProxyTarget =
  process.env.BLAST_ECOM_API_PROXY_TARGET ?? 'http://127.0.0.1:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': apiProxyTarget,
      '/admin': apiProxyTarget,
      '/static': apiProxyTarget,
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    restoreMocks: true,
    exclude: [...configDefaults.exclude, 'e2e/**'],
  },
})
