/// <reference types="vitest/config" />
import path from 'path';
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

// Test toolchain for the repo (spec.md C10).
// Execution ships the runner only; Verification adds the test files under tests/.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // Mirrors tsconfig.json "paths": { "@/*": ["./*"] }
      '@': path.resolve(__dirname, '.'),
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: [path.resolve(__dirname, 'vitest.setup.ts')],
    passWithNoTests: true,
    // Intentionally left at Vitest's default `include` glob so a test file placed
    // anywhere in the repo is picked up rather than silently ignored.
    css: false,
  },
});
