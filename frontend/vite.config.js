import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const apiProxy = {
  target: 'http://127.0.0.1:8000',
  changeOrigin: true,
  configure(proxy) {
    proxy.on('proxyReq', (proxyReq, req) => {
      const auth = req.headers.authorization
      if (auth) {
        proxyReq.setHeader('authorization', auth)
      }
    })
  },
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Same-origin /api in dev → FastAPI (avoids CORS when using 127.0.0.1 vs localhost)
      '/api': apiProxy,
      // Jinja-only FastAPI paths (do NOT proxy all `/customer` — React owns `/customer/payment/*`, etc.)
      '/customer/chatbot': apiProxy,
      '/customer/messages': apiProxy,
      '/customer/message': apiProxy,
    },
  },
  preview: {
    proxy: {
      '/api': apiProxy,
      '/customer/chatbot': apiProxy,
      '/customer/messages': apiProxy,
      '/customer/message': apiProxy,
    },
  },
})
