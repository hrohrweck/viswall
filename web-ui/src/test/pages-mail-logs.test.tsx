import { beforeAll, afterAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { http, HttpResponse } from 'msw'

import { MailDomains } from '../pages/Mail/MailDomains'
import { useInstanceStore } from '../stores/instance'
import { server } from './msw/node'

/* ------------------------------------------------------------------ */
/*  ResizeObserver polyfill — Radix useSize                            */
/* ------------------------------------------------------------------ */

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

/* ------------------------------------------------------------------ */
/*  IntersectionObserver mock — jsdom has none (vitest.config runs     */
/*  jsdom). Instances are recorded so tests can fire the callback at   */
/*  the sentinel deterministically.                                    */
/* ------------------------------------------------------------------ */

class MockIntersectionObserver {
  static instances: MockIntersectionObserver[] = []
  callback: IntersectionObserverCallback
  constructor(callback: IntersectionObserverCallback) {
    this.callback = callback
    MockIntersectionObserver.instances.push(this)
  }
  observe() {}
  unobserve() {}
  disconnect() {}
}

beforeAll(() => {
  vi.stubGlobal('IntersectionObserver', MockIntersectionObserver)
})
afterAll(() => {
  vi.unstubAllGlobals()
})

/** Fires the latest observer as if the sentinel became visible. */
function fireSentinel() {
  const instances = MockIntersectionObserver.instances
  const io = instances[instances.length - 1]
  if (!io) throw new Error('no IntersectionObserver instance created')
  io.callback(
    [{ isIntersecting: true }] as unknown as IntersectionObserverEntry[],
    io as unknown as IntersectionObserver,
  )
}

const flush = (ms = 30) => new Promise((r) => setTimeout(r, ms))

const lastUrl = (urls: URL[]): URL | undefined => urls[urls.length - 1]

/* ------------------------------------------------------------------ */
/*  sonner mock                                                        */
/* ------------------------------------------------------------------ */

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    warning: vi.fn(),
    loading: vi.fn(),
    dismiss: vi.fn(),
    message: vi.fn(),
    promise: vi.fn(),
    custom: vi.fn(),
  },
  Toaster: () => null,
}))

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
}

function Wrapper({ children }: { children: React.ReactNode }) {
  const qc = makeQueryClient()
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        {children}
      </MemoryRouter>
    </QueryClientProvider>
  )
}

function setInstance(id: number | null) {
  useInstanceStore.setState({ selectedInstanceId: id })
}

/**
 * Paginated /mail/logs mock: page 1 (offset 0) → 200 lines + next_offset 200;
 * page 2 → 150 lines + next_offset null (end sentinel). Records every request
 * URL so tests can assert exact offset/limit/q params.
 */
function useLogsHandler() {
  const requests: URL[] = []
  const handler = http.get('*/mail/logs/:instanceId', ({ request }) => {
    const url = new URL(request.url)
    requests.push(url)
    const offset = Number(url.searchParams.get('offset') ?? '0')
    if (offset === 0) {
      return HttpResponse.json({
        lines: Array.from({ length: 200 }, (_, i) => `LOG LINE ${i}`),
        total_matched: 350,
        next_offset: 200,
      })
    }
    return HttpResponse.json({
      lines: Array.from({ length: 150 }, (_, i) => `LOG LINE ${offset + i}`),
      total_matched: 350,
      next_offset: null,
    })
  })
  return { requests, handler }
}

/** Renders the Mail page with instance 1 selected and waits for the domains table. */
async function renderMailPage() {
  render(<MailDomains />, { wrapper: Wrapper })
  await waitFor(() => {
    expect(screen.getByText('example.test')).toBeInTheDocument()
  })
}

beforeEach(() => {
  setInstance(1)
  MockIntersectionObserver.instances = []
})

/* ================================================================== */
/*  1 — Tabs render; default tab = domains                             */
/* ================================================================== */

describe('Mail page tabs', () => {
  it('renders both tabs with Mail Domains active by default', async () => {
    await renderMailPage()

    expect(screen.getByRole('tab', { name: 'Mail Domains' })).toHaveAttribute(
      'data-state',
      'active',
    )
    expect(screen.getByRole('tab', { name: 'Logs' })).toBeInTheDocument()
    // Domains table visible; no log content mounted
    expect(screen.getByText('example.test')).toBeInTheDocument()
    expect(screen.queryByText('LOG LINE 0')).not.toBeInTheDocument()
  })

  it('shows the no-instance guard above the tabs', async () => {
    setInstance(null)
    render(<MailDomains />, { wrapper: Wrapper })
    expect(
      screen.getByText('Select an instance from the top bar to manage its mail domains.'),
    ).toBeInTheDocument()
    expect(screen.queryByRole('tab', { name: 'Logs' })).not.toBeInTheDocument()
  })
})

/* ================================================================== */
/*  2 — Logs tab fetches page 1 with exact params                      */
/* ================================================================== */

describe('Logs panel first page', () => {
  it('requests /mail/logs/1?offset=0&limit=200 and renders the lines', async () => {
    const { requests, handler } = useLogsHandler()
    server.use(handler)

    await renderMailPage()
    await userEvent.click(screen.getByRole('tab', { name: 'Logs' }))

    await waitFor(() => {
      expect(screen.getByText('LOG LINE 199')).toBeInTheDocument()
    })
    expect(screen.getByText('LOG LINE 0')).toBeInTheDocument()

    expect(requests).toHaveLength(1)
    expect(requests[0].pathname).toBe('/api/v1/mail/logs/1')
    expect(requests[0].searchParams.get('offset')).toBe('0')
    expect(requests[0].searchParams.get('limit')).toBe('200')
    expect(screen.getByText('350 lines matched')).toBeInTheDocument()
  })
})

/* ================================================================== */
/*  3 — Endless scroll: IO-triggered append, stop at null sentinel     */
/* ================================================================== */

describe('Logs panel endless scroll', () => {
  it('appends page 2 on sentinel intersection and stops at the null sentinel', async () => {
    const { requests, handler } = useLogsHandler()
    server.use(handler)

    await renderMailPage()
    await userEvent.click(screen.getByRole('tab', { name: 'Logs' }))
    await waitFor(() => {
      expect(screen.getByText('LOG LINE 199')).toBeInTheDocument()
    })

    fireSentinel()

    await waitFor(() => {
      expect(screen.getByText('LOG LINE 200')).toBeInTheDocument()
    })
    expect(screen.getByText('LOG LINE 349')).toBeInTheDocument()
    expect(requests).toHaveLength(2)
    expect(requests[1].searchParams.get('offset')).toBe('200')

    // End sentinel: next_offset null → the panel shows End of logs and a
    // further sentinel intersection makes no additional request.
    expect(screen.getByText('End of logs')).toBeInTheDocument()
    fireSentinel()
    await flush()
    await flush()
    expect(requests).toHaveLength(2)
  })
})

/* ================================================================== */
/*  4 — Keyword filter + Clear Filters                                 */
/* ================================================================== */

describe('Logs panel filters', () => {
  it('debounces the keyword into the q param and clears it on Clear Filters', async () => {
    const { requests, handler } = useLogsHandler()
    server.use(handler)

    await renderMailPage()
    await userEvent.click(screen.getByRole('tab', { name: 'Logs' }))
    await waitFor(() => {
      expect(screen.getByText('LOG LINE 0')).toBeInTheDocument()
    })
    expect(lastUrl(requests)?.searchParams.get('q')).toBeNull()
    expect(screen.getByRole('button', { name: 'Clear Filters' })).toBeDisabled()

    await userEvent.type(screen.getByLabelText('Keyword'), 'bounce')

    await waitFor(() => {
      expect(lastUrl(requests)?.searchParams.get('q')).toBe('bounce')
    })
    expect(screen.getByRole('button', { name: 'Clear Filters' })).toBeEnabled()

    await userEvent.click(screen.getByRole('button', { name: 'Clear Filters' }))

    await waitFor(() => {
      const last = lastUrl(requests)
      expect(last?.searchParams.get('q')).toBeNull()
      expect(last?.searchParams.get('offset')).toBe('0')
    })
    expect(screen.getByRole('button', { name: 'Clear Filters' })).toBeDisabled()
  })
})

/* ================================================================== */
/*  5 — Zero mail domains → no Logs tab                                */
/* ================================================================== */

describe('Logs tab gating', () => {
  it('hides the Logs tab when the instance has no mail domains', async () => {
    server.use(
      http.get('*/mail/domains/:instanceId', () => HttpResponse.json([])),
    )
    render(<MailDomains />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByText('No mail domains')).toBeInTheDocument()
    })
    expect(screen.queryByRole('tab', { name: 'Logs' })).not.toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Mail Domains' })).toBeInTheDocument()
  })
})

/* ================================================================== */
/*  6 — Agent 502 → error state inside the panel, page alive           */
/* ================================================================== */

describe('Logs panel agent error', () => {
  it('shows the QueryError inside the panel without crashing the page', async () => {
    server.use(
      http.get('*/mail/logs/:instanceId', () =>
        HttpResponse.json(
          { detail: 'mail agent unreachable or logs endpoint unavailable' },
          { status: 502 },
        ),
      ),
    )

    await renderMailPage()
    await userEvent.click(screen.getByRole('tab', { name: 'Logs' }))

    await waitFor(() => {
      expect(screen.getByText('Log agent unreachable')).toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument()
    // Page shell intact
    expect(screen.getByRole('tab', { name: 'Mail Domains' })).toBeInTheDocument()
  })
})
