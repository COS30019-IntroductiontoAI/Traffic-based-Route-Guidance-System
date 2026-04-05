import { defineConfig } from 'vite'
import react, { reactCompilerPreset } from '@vitejs/plugin-react'
import babel from '@rolldown/plugin-babel'
import path from 'path'
import { fileURLToPath } from 'url'

const frontendDir = path.dirname(fileURLToPath(import.meta.url))

// https://vite.dev/config/
export default defineConfig({
  base: '/Traffic-based-Route-Guidance-System/',
  root: frontendDir,
  build: {
    outDir: path.resolve(frontendDir, '../docs'),
    emptyOutDir: true,
  },
  plugins: [
    react(),
    babel({ presets: [reactCompilerPreset()] }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(frontendDir, './src'),
    },
  },
  css: {
    postcss: path.resolve(frontendDir, './postcss.config.js'),
  },
})
