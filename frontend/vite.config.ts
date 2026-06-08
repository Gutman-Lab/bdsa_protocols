import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const frontendRoot = path.dirname(fileURLToPath(import.meta.url))
// Docker sets BDSA_COMPONENTS_ROOT=/bdsa-react-components; local dev uses sibling repo
const componentsRoot = process.env.BDSA_COMPONENTS_ROOT
  ? path.resolve(process.env.BDSA_COMPONENTS_ROOT)
  : path.resolve(frontendRoot, '../../bdsa-react-components')

const componentsEntry = path.join(componentsRoot, 'src/index.ts')
const componentsStyles = path.join(componentsRoot, 'dist/index.css')

const hmrHost = process.env.VITE_HMR_HOST || 'localhost'
const hmrClientPort = Number(process.env.VITE_HMR_CLIENT_PORT || 3000)
const hmrProtocol = process.env.VITE_HMR_PROTOCOL as 'ws' | 'wss' | undefined

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  appType: 'spa',
  resolve: {
    alias: [
      { find: 'bdsa-react-components/styles.css', replacement: componentsStyles },
      { find: 'bdsa-react-components', replacement: componentsEntry },
    ],
    dedupe: ['react', 'react-dom'],
  },
  optimizeDeps: {
    // Pre-bundle the library from source, not the 2MB dist + broken source maps
    exclude: ['bdsa-react-components'],
  },
  server: {
    port: 3000,
    host: true,
    allowedHosts: ['schema.bdsa.io'],
    strictPort: true,
    open: process.env.VITE_OPEN_BROWSER === 'true',
    fs: {
      allow: [frontendRoot, componentsRoot, path.join(componentsRoot, '..'), path.join(componentsRoot, 'old-src')],
    },
    watch: {
      usePolling: process.env.CHOKIDAR_USEPOLLING === 'true',
    },
    hmr: {
      host: hmrHost,
      clientPort: hmrClientPort,
      ...(hmrProtocol ? { protocol: hmrProtocol } : {}),
    },
    proxy: {
      '/api': {
        target: process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  preview: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
