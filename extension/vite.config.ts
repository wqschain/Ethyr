import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig({
  plugins: [
    react(),
    {
      name: 'copy-files',
      async writeBundle() {
        // Copy manifest.json and icons to dist
        const fs = await import('fs/promises');
        await fs.copyFile('manifest.json', 'dist/manifest.json');
        
        // Create icons directory if it doesn't exist
        await fs.mkdir('dist/icons', { recursive: true });
        
        // Copy icons if they exist
        try {
          await fs.copyFile('icons/icon16.png', 'dist/icons/icon16.png');
          await fs.copyFile('icons/icon48.png', 'dist/icons/icon48.png');
          await fs.copyFile('icons/icon128.png', 'dist/icons/icon128.png');
          await fs.copyFile('icons/ethyrlogo.png', 'dist/icons/ethyrlogo.png');
        } catch (e) {
          console.warn('Some icons not found:', e);
        }
      }
    }
  ],
  build: {
    outDir: 'dist',
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html')
      },
      output: {
        entryFileNames: `assets/[name].js`,
        chunkFileNames: `assets/[name].js`,
        assetFileNames: `assets/[name].[ext]`
      }
    }
  },
  server: {
    port: 3000
  }
}); 