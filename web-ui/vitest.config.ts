/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { configDefaults } from 'vitest/config'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    exclude: [...configDefaults.exclude, 'e2e/**'],
    // Dialog-interaction tests (userEvent chains + waitFor) routinely exceed
    // vitest's 5s default on the loaded shared CI agent; failures rotated
    // between unrelated test files across runs.
    testTimeout: 20_000,
  },
})
