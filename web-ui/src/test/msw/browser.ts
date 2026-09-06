import { setupWorker } from 'msw/browser'
import { handlers } from './handlers'

/**
 * Browser-side MSW worker for local dev / Playwright e2e runs.
 * Started only from src/main.tsx when the app runs with
 * `VITE_ENABLE_MSW=1 npm run dev` — the import is behind a static
 * `import.meta.env.DEV` gate, so this module (and all of msw) is tree-shaken
 * out of production builds. Unhandled requests bypass the worker and fall
 * through to the Vite proxy (or the real backend).
 */
export const worker = setupWorker(...handlers)

export function startMockWorker(): Promise<ServiceWorkerRegistration | undefined> {
  return worker.start({ onUnhandledRequest: 'bypass' })
}
