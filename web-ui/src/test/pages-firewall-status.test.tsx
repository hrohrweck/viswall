import { beforeEach, describe, expect, it } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { http, HttpResponse } from 'msw'
import { server } from './msw/node'
import { useInstanceStore } from '../stores/instance'
import { FirewallRules } from '../pages/FirewallRules'

/**
 * FirewallRules agent-status card + rollback control — Task 29.
 *
 * The status card is fed by GET /firewall/stats/:instanceId (the gateway
 * passthrough that exists at HEAD). The agent payload shape
 * ({nftables, connections{tracked,max}, timestamp}) renders the online badge;
 * the gateway zeroed fallback renders offline; a 500 renders error; and the
 * optional apply_error field renders a danger strip when present.
 *
 * The rollback button must NOT post without an explicit confirm — the
 * recorder handler proves the POST only fires after the dialog confirm.
 */

const onlineStats = {
  nftables: { nftables: [{ metainfo: { version: '1.0.9' } }] },
  connections: { tracked: 42, max: 262144 },
  timestamp: '2026-10-22T21:48:57.197326+00:00',
}

const offlineStats = {
  instance_id: 1,
  connections: 0,
  packets_accepted: 0,
  packets_dropped: 0,
  blacklist_size: 0,
  top_blocked_ips: [],
}

function createWrapper() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={qc}>
        <MemoryRouter>{children}</MemoryRouter>
      </QueryClientProvider>
    )
  }
}

beforeEach(() => {
  useInstanceStore.setState({ selectedInstanceId: 1 })
  server.use(
    http.get('/api/v1/firewall/stats/:instanceId', () => HttpResponse.json(onlineStats)),
  )
})

describe('FirewallRules agent status card', () => {
  it('renders online badge + connection stats for the agent payload shape', async () => {
    const Wrapper = createWrapper()
    render(<FirewallRules />, { wrapper: Wrapper })

    await screen.findByText('online')
    expect(screen.getByText('42')).toBeInTheDocument()
    expect(screen.getByText('262144')).toBeInTheDocument()
  })

  it('renders offline badge for the gateway zeroed fallback shape', async () => {
    server.use(
      http.get('/api/v1/firewall/stats/:instanceId', () => HttpResponse.json(offlineStats)),
    )

    const Wrapper = createWrapper()
    render(<FirewallRules />, { wrapper: Wrapper })

    await screen.findByText('offline')
  })

  it('renders error badge when the stats request fails', async () => {
    server.use(
      http.get('/api/v1/firewall/stats/:instanceId', () => new HttpResponse(null, { status: 500 })),
    )

    const Wrapper = createWrapper()
    render(<FirewallRules />, { wrapper: Wrapper })

    await screen.findByText('error')
  })

  it('renders apply_error as a danger strip when the payload carries it', async () => {
    server.use(
      http.get('/api/v1/firewall/stats/:instanceId', () =>
        HttpResponse.json({
          ...onlineStats,
          apply_error: 'nftables validation failed: syntax error',
        }),
      ),
    )

    const Wrapper = createWrapper()
    render(<FirewallRules />, { wrapper: Wrapper })

    await screen.findByText(/Last apply failed: nftables validation failed/)
  })
})

describe('FirewallRules rollback control', () => {
  it('posts to /firewall/rollback/1 only after dialog confirm', async () => {
    let capturedPath = ''
    server.use(
      http.post('/api/v1/firewall/rollback/:instanceId', ({ request }) => {
        capturedPath = new URL(request.url).pathname
        return HttpResponse.json({ restored: true, mechanism: 'direct (snapshot files)' })
      }),
    )

    const Wrapper = createWrapper()
    render(<FirewallRules />, { wrapper: Wrapper })

    await screen.findByText('online')

    await userEvent.click(screen.getByRole('button', { name: /rollback last apply/i }))

    const dialog = await screen.findByRole('dialog')
    expect(dialog).toHaveTextContent(/snapshot taken before the last apply/)
    expect(capturedPath).toBe('')

    const confirmBtn = Array.from(dialog.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Rollback') && !b.textContent?.includes('Cancel'),
    )
    await userEvent.click(confirmBtn!)

    await waitFor(() => {
      expect(capturedPath).toBe('/api/v1/firewall/rollback/1')
    })
  })

  it('cancel closes the dialog without posting', async () => {
    let capturedPath = ''
    server.use(
      http.post('/api/v1/firewall/rollback/:instanceId', ({ request }) => {
        capturedPath = new URL(request.url).pathname
        return HttpResponse.json({ restored: true })
      }),
    )

    const Wrapper = createWrapper()
    render(<FirewallRules />, { wrapper: Wrapper })

    await screen.findByText('online')

    await userEvent.click(screen.getByRole('button', { name: /rollback last apply/i }))
    await screen.findByRole('dialog')
    await userEvent.click(screen.getByRole('button', { name: 'Cancel' }))

    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })
    expect(capturedPath).toBe('')
  })
})
