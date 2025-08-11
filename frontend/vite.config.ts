import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: 'localhost',
    strictPort: true, // 포트 3000이 사용 중이면 에러 발생 (자동 변경 방지)
    hmr: {
      overlay: true
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      // 백엔드 API 엔드포인트들 직접 프록시
      '/scrape': 'http://localhost:8000',
      '/jobs': 'http://localhost:8000',
      '/stats': 'http://localhost:8000',
      '/job': 'http://localhost:8000',
      '/download': 'http://localhost:8000'
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
})