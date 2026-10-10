import '@testing-library/jest-dom'
import { cleanup, configure } from '@testing-library/react'
import { afterAll, afterEach, beforeAll } from 'vitest'
import { server } from './msw/node'

// React Testing Library + user-event + MSW (node) QA harness.
// - jest-dom matchers and RTL cleanup are registered globally for every test.
// - user-event is used per-test via `userEvent.setup()` (see msw-smoke.test.tsx).
// - MSW intercepts all /api/v1/* traffic with the deterministic fixture set
//   (src/test/msw/fixtures.ts). Requests without a matching handler bypass
//   the mock layer, so tests that don't need the API stay unaffected.
// - findBy*/waitFor retry for only 1s by default, which the initial
//   MSW-served render regularly exceeds on the loaded shared CI agent —
//   failures rotated between unrelated test files ("Unable to find an
//   element with the text: …"). Give async utilities a proper budget.
configure({ asyncUtilTimeout: 5000 })

beforeAll(() => {
  server.listen({ onUnhandledRequest: 'bypass' })
})

afterEach(() => {
  cleanup()
  server.resetHandlers()
})

afterAll(() => {
  server.close()
})
