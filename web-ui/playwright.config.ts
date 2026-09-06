import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright e2e config for the MSW-seeded QA harness.
 *
 * The webServer command matches vite.config.ts (port 3000 — NOT the Vite
 * default 5173). `reuseExistingServer: true` lets local runs reuse a dev
 * server you already started with `VITE_ENABLE_MSW=1 npm run dev` (required
 * for the MSW browser worker to be active). When Playwright spawns the
 * server itself it uses the plain dev command, so start the MSW-enabled
 * server yourself for specs that depend on fixtures.
 */
export default defineConfig({
  testDir: 'e2e',
  timeout: 30_000,
  expect: { timeout: 10_000 },
  fullyParallel: true,
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'retain-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: true,
    timeout: 120_000,
  },
})
