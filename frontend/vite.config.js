import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Docker Desktop on Windows doesn't forward inotify events across bind
    // mounts, so Vite's default watcher misses file changes. Polling works
    // around it.
    watch: {
      usePolling: true,
    },
  },
})
