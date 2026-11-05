import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { handleApiRequest } from './server/app.js'

const kioscoApiPlugin = () => ({
  name: 'kiosco-api-middleware',
  configureServer(server) {
    server.middlewares.use((req, res, next) => {
      if (req.url && req.url.startsWith('/api/')) {
        return handleApiRequest(req, res)
      }
      next()
    })
  }
})

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), kioscoApiPlugin()],
})
