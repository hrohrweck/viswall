import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright e2e config for the MSW-seeded QA harness.
 *
 * The webServer pins an explicit IPv4 loopback host + port with --strictPort:
 * on this machine 127.0.0.1:3000 is hijacked by a Rancher Desktop ssh
 * local-forward serving a foreign Next.js app, and `localhost:3000` resolves
 * inconsistently between Node (readiness probe) and Chromium (test traffic).
 * With reuseExistingServer disabled, Playwright always spawns OUR vite on
 * 127.0.0.1:5180 and fails loudly if that port is taken — never silently
 * testing whatever else answers on a well-known port.
 *
 * The command enables the MSW browser worker (VITE_ENABLE_MSW=1) so specs
 * run against the deterministic fixture set without a backend.
 */
export default defineConfig({
  testDir: 'e2e',
  timeout: 30_000,
  expect: { timeout: 10_000 },
  fullyParallel: true,
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: 'http://127.0.0.1:5180',
    trace: 'retain-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: 'VITE_ENABLE_MSW=1 npm run dev -- --host 127.0.0.1 --port 5180 --strictPort',
    url: 'http://127.0.0.1:5180',
    reuseExistingServer: false,
    timeout: 120_000,
  },
})
