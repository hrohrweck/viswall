import { setupServer } from 'msw/node'
import { handlers } from './handlers'

/**
 * Node-side MSW server for vitest (jsdom) component tests.
 * Lifecycle is managed globally in src/test/setup.ts.
 */
export const server = setupServer(...handlers)
