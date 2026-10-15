import { existsSync, readdirSync, unlinkSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// PNG cutout pemain (17,9 MB) hanya dipakai sbg cadangan di dev; tampilan memakai
// varian WebP hasil scripts/optimize_player_images.py. Buang PNG dari dist agar
// build akhir tetap ringan — aset di folder public/ TIDAK disentuh.
function dropPlayerPngFromDist() {
  return {
    name: 'drop-player-png-from-dist',
    apply: 'build',
    closeBundle() {
      const dir = join(process.cwd(), 'dist', 'assets', 'players')
      if (!existsSync(dir)) return
      let removed = 0
      for (const f of readdirSync(dir)) {
        if (f.toLowerCase().endsWith('.png')) {
          unlinkSync(join(dir, f))
          removed++
        }
      }
      if (removed) console.log(`  [drop-player-png] ${removed} PNG cadangan dibuang dari dist`)
    },
  }
}

export default defineConfig({
  plugins: [vue(), dropPlayerPngFromDist()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5174,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
    },
  },
})
