import { beforeAll, afterAll, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { http, HttpResponse } from 'msw'

import { LLMConfiguration } from '../pages/admin/LLMConfiguration'
import { FirewallSimulator } from '../pages/Firewall/FirewallSimulator'
import { FirewallTestSuite } from '../pages/Firewall/FirewallTestSuite'
import { server } from './msw/node'

/* -------------------------------------------------------------------------- */
/*  ResizeObserver polyfill — Tooltip → Radix useSize                         */
/* -------------------------------------------------------------------------- */

let originalResizeObserver: typeof globalThis.ResizeObserver
beforeAll(() => {
  originalResizeObserver = globalThis.ResizeObserver
  globalThis.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as unknown as typeof globalThis.ResizeObserver
})
afterAll(() => {
  globalThis.ResizeObserver = originalResizeObserver
})

/* -------------------------------------------------------------------------- */
/*  LLM fixture data (local to this test — not in shared fixtures)            */
/* -------------------------------------------------------------------------- */

const mockProviders = [
  {
    id: 1,
    name: 'Local Ollama',
    provider_type: 'ollama',
    base_url: 'http://ollama:11434',
    api_key: null,
    is_enabled: true,
    is_default: true,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
  {
    id: 2,
    name: 'OpenAI Production',
    provider_type: 'openai',
    base_url: null,
    api_key: 'sk-test',
    is_enabled: true,
    is_default: false,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
]

const mockModels = [
  {
    id: 1,
    provider_id: 1,
    name: 'qwen3.5:9b',
    display_name: 'Qwen 3.5 9B',
    description: 'Email classification',
    max_tokens: 4096,
    supports_vision: false,
    is_enabled: true,
    created_at: '2026-01-01T00:00:00Z',
  },
]

const mockUseCases = [
  {
    id: 1,
    use_case: 'email_classification',
    provider_id: 1,
    model_id: 1,
    temperature: 0.3,
    max_tokens: 500,
    top_p: 0.9,
    system_prompt: 'Classify the following email.',
    timeout_seconds: 30,
    is_enabled: true,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
]

/* -------------------------------------------------------------------------- */
/*  MSW handlers for LLM admin endpoints                                     */
/* -------------------------------------------------------------------------- */

function installLLMHandlers() {
  server.use(
    http.get('/api/v1/admin/llm/providers', () =>
      HttpResponse.json(mockProviders),
    ),
    http.get('/api/v1/admin/llm/models', () =>
      HttpResponse.json(mockModels),
    ),
    http.get('/api/v1/admin/llm/use-cases', () =>
      HttpResponse.json(mockUseCases),
    ),
    http.post('/api/v1/admin/llm/providers/:id/test', () =>
      HttpResponse.json({ status: 'ok', response: 'Model responded correctly' }),
    ),
    http.delete('/api/v1/admin/llm/providers/:id', () =>
      HttpResponse.json(null, { status: 204 }),
    ),
  )
}

/* -------------------------------------------------------------------------- */
/*  Helpers                                                                    */
/* -------------------------------------------------------------------------- */

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>{children}</MemoryRouter>
      </QueryClientProvider>
    )
  }
}

/* -------------------------------------------------------------------------- */
/*  LLMConfiguration tests                                                    */
/* -------------------------------------------------------------------------- */

describe('LLMConfiguration', () => {
  it('renders providers table with searchable DataTable', async () => {
    installLLMHandlers()
    const Wrapper = createWrapper()
    render(<LLMConfiguration />, { wrapper: Wrapper })

    // PageHeader
    expect(
      screen.getByRole('heading', { name: /llm providers/i }),
    ).toBeInTheDocument()

    // Wait for data
    await screen.findByText('Local Ollama')
    expect(screen.getByText('OpenAI Production')).toBeInTheDocument()

    // Searchable input present
    expect(screen.getByRole('textbox', { name: /search/i })).toBeInTheDocument()
  })

  it('tabs switch between Providers, Models, and Use Cases', async () => {
    installLLMHandlers()
    const user = userEvent.setup()
    const Wrapper = createWrapper()
    render(<LLMConfiguration />, { wrapper: Wrapper })

    await screen.findByText('Local Ollama')

    // Click Models tab
    const modelsTab = screen.getByRole('tab', { name: /models/i })
    await user.click(modelsTab)

    await waitFor(() => {
      expect(screen.getByText('qwen3.5:9b')).toBeInTheDocument()
    })

    // Click Use Cases tab
    const useCasesTab = screen.getByRole('tab', { name: /use cases/i })
    await user.click(useCasesTab)

    await waitFor(() => {
      expect(screen.getByText('Email Classification')).toBeInTheDocument()
    })
  })

  it('delete opens ConfirmDialog — native confirm is NEVER called', async () => {
    installLLMHandlers()
    const confirmSpy = vi.spyOn(window, 'confirm')
    const user = userEvent.setup()
    const Wrapper = createWrapper()
    render(<LLMConfiguration />, { wrapper: Wrapper })

    await screen.findByText('Local Ollama')

    // Click the delete button (first trash icon)
    const deleteButtons = screen.getAllByRole('button', { name: /delete/i })
    await user.click(deleteButtons[0])

    // ConfirmDialog should appear
    await waitFor(() => {
      expect(
        screen.getByRole('dialog', { name: /delete provider/i }),
      ).toBeInTheDocument()
    })

    // Native confirm must NEVER have been called
    expect(confirmSpy).not.toHaveBeenCalled()
    confirmSpy.mockRestore()
  })

  it('test renders per-provider result (not global banner)', async () => {
    installLLMHandlers()
    const user = userEvent.setup()
    const Wrapper = createWrapper()
    render(<LLMConfiguration />, { wrapper: Wrapper })

    await screen.findByText('Local Ollama')

    // Click the test button on first provider row
    const testButtons = screen.getAllByRole('button', {
      name: /test connection/i,
    })
    await user.click(testButtons[0])

    // Per-provider result appears (inline alert, not global)
    await waitFor(() => {
      expect(
        screen.getByText(/connection successful/i),
      ).toBeInTheDocument()
    })

    // Result message from mock
    expect(
      screen.getByText('Model responded correctly'),
    ).toBeInTheDocument()

    // Should NOT be a global banner at the top — the alert should have role="alert"
    const alerts = screen.getAllByRole('alert')
    expect(alerts.length).toBeGreaterThanOrEqual(1)
  })
})

/* -------------------------------------------------------------------------- */
/*  Firewall preview notice tests                                             */
/* -------------------------------------------------------------------------- */

describe('FirewallSimulator', () => {
  it('renders the Preview notice', () => {
    const Wrapper = createWrapper()
    render(<FirewallSimulator />, { wrapper: Wrapper })

    expect(
      screen.getByText(/preview — not connected to a live instance/i),
    ).toBeInTheDocument()
  })
})

describe('FirewallTestSuite', () => {
  it('renders the Preview notice', () => {
    const Wrapper = createWrapper()
    render(<FirewallTestSuite />, { wrapper: Wrapper })

    expect(
      screen.getByText(/preview — not connected to a live instance/i),
    ).toBeInTheDocument()
  })

  it('Export Report button is absent', () => {
    const Wrapper = createWrapper()
    render(<FirewallTestSuite />, { wrapper: Wrapper })

    expect(
      screen.queryByRole('button', { name: /export report/i }),
    ).not.toBeInTheDocument()
  })
})
