import { describe, it, expect } from 'vitest'
import { router } from '../router'

describe('App smoke test', () => {
  it('router should be defined with routes', () => {
    expect(router).toBeDefined()
    expect(router.routes.length).toBeGreaterThan(0)
  })

  it('should import main entry point dependencies without error', async () => {
    const { StrictMode } = await import('react')
    const { QueryClient } = await import('@tanstack/react-query')
    expect(StrictMode).toBeDefined()
    expect(QueryClient).toBeDefined()
  })
})
