import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/checkout': 'http://127.0.0.1:8000',
      '/login': 'http://127.0.0.1:8000',
      '/register': 'http://127.0.0.1:8000',
      '/order-history': 'http://127.0.0.1:8000',
      '/staff-dashboard': 'http://127.0.0.1:8000',
      '/subscribe': 'http://127.0.0.1:8000',
      '/track-order': 'http://127.0.0.1:8000',
      '/support': 'http://127.0.0.1:8000',
      '/static': 'http://127.0.0.1:8000'
    }
  }
});
