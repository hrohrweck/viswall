import { beforeAll, afterAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { http, HttpResponse } from 'msw'

import { DHCPServers } from '../pages/DHCP/DHCPServers'
import { useInstanceStore } from '../stores/instance'
import { server } from './msw/node'

/* -------------------------------------------------------------------------- */
/*  ResizeObserver polyfill — IconButton wraps Tooltip → Radix useSize         */
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
/*  Helpers                                                                    */
/* -------------------------------------------------------------------------- */

function renderDHCP() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <DHCPServers />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

/** Select server kea-main → subnet lan-v4 so pools/leases panes hydrate. */
async function selectFirstSubnet() {
  await screen.findByText('kea-main')
  await userEvent.click(screen.getByText('kea-main'))
  await screen.findByText('lan-v4')
  await userEvent.click(screen.getByText('lan-v4'))
}

/* -------------------------------------------------------------------------- */
/*  Test suite                                                                 */
/* -------------------------------------------------------------------------- */

describe('DHCP Management page', () => {
  beforeEach(() => {
    useInstanceStore.setState({ selectedInstanceId: 1 })
  })

  /* ── 1. Start action opens ConfirmDialog before firing ──────────────── */
  it('Start server opens ConfirmDialog before firing', async () => {
    const mutateSpy = vi.fn()
    server.use(
      http.post('*/dhcp/servers/:id/actions/start', async () => {
        mutateSpy()
        return HttpResponse.json({ status: 'started' })
      }),
    )

    renderDHCP()
    await screen.findByText('kea-main')

    const startBtn = screen.getByRole('button', { name: /start server/i })
    await userEvent.click(startBtn)

    const dialog = await screen.findByRole('dialog')
    expect(dialog).toBeInTheDocument()
    expect(mutateSpy).not.toHaveBeenCalled()
  })

  /* ── 2. Reload action opens ConfirmDialog before firing ─────────────── */
  it('Reload server opens ConfirmDialog before firing', async () => {
    const mutateSpy = vi.fn()
    server.use(
      http.post('*/dhcp/servers/:id/actions/reload', async () => {
        mutateSpy()
        return HttpResponse.json({ status: 'reloaded' })
      }),
    )

    renderDHCP()
    await screen.findByText('kea-main')

    const reloadBtn = screen.getByRole('button', { name: /reload server/i })
    await userEvent.click(reloadBtn)

    const dialog = await screen.findByRole('dialog')
    expect(dialog).toBeInTheDocument()
    expect(mutateSpy).not.toHaveBeenCalled()
  })

  /* ── 3. Stop action: full dialog flow (confirm fires mutation) ──────── */
  it('Stop server confirms before firing the mutation', async () => {
    const mutateSpy = vi.fn()
    server.use(
      http.post('*/dhcp/servers/:id/actions/stop', async () => {
        mutateSpy()
        return HttpResponse.json({ status: 'stopped' })
      }),
    )

    renderDHCP()
    await screen.findByText('kea-main')

    const stopBtn = screen.getByRole('button', { name: /stop server/i })
    await userEvent.click(stopBtn)

    const dialog = await screen.findByRole('dialog')
    expect(dialog).toBeInTheDocument()
    expect(mutateSpy).not.toHaveBeenCalled()

    const confirmBtn = within(dialog).getByRole('button', { name: /stop/i })
    await userEvent.click(confirmBtn)

    await waitFor(() => expect(mutateSpy).toHaveBeenCalledTimes(1))
  })

  /* ── 4. Release lease: ConfirmDialog with impact text ────────────────── */
  it('Release lease confirms with impact text before firing', async () => {
    const mutateSpy = vi.fn()
    server.use(
      http.delete('*/dhcp/leases/:leaseId', async () => {
        mutateSpy()
        return HttpResponse.json({
          id: 1,
          state: 'released',
          released_at: '2026-01-05T12:30:00.000Z',
        })
      }),
    )

    renderDHCP()
    await selectFirstSubnet()
    await screen.findByText('192.168.1.101')

    const releaseBtns = screen.getAllByRole('button', { name: /release/i })
    await userEvent.click(releaseBtns[0])

    const dialog = await screen.findByRole('dialog')
    expect(dialog).toHaveTextContent(/Releases lease 192\.168\.1\.101/)
    expect(dialog).toHaveTextContent(/re-request an IP address/)
    expect(mutateSpy).not.toHaveBeenCalled()

    const confirmBtn = within(dialog).getByRole('button', { name: /release/i })
    await userEvent.click(confirmBtn)

    await waitFor(() => expect(mutateSpy).toHaveBeenCalledTimes(1))
  })

  /* ── 5. Selecting a subnet loads the pools pane ──────────────────────── */
  it('selecting a subnet loads pools pane', async () => {
    renderDHCP()
    await selectFirstSubnet()

    await waitFor(() => {
      expect(screen.getByText('192.168.1.100 - 192.168.1.199')).toBeInTheDocument()
    })
  })

  /* ── 6. Create Server form submits expected payload ──────────────────── */
  it('Create Server form submits expected payload', async () => {
    let capturedPayload: Record<string, unknown> | null = null
    server.use(
      http.post('*/dhcp/servers/:instanceId', async ({ request }) => {
        capturedPayload = (await request.json()) as Record<string, unknown>
        return HttpResponse.json({
          id: 99,
          instance_id: 1,
          name: 'kea-dhcp-1',
          status: 'stopped',
          subnets_count: 0,
          ...capturedPayload,
        })
      }),
    )

    renderDHCP()
    await screen.findByText('kea-main')

    await userEvent.click(screen.getByRole('button', { name: /new dhcp server/i }))

    const dialog = await screen.findByRole('dialog')
    const submitBtn = within(dialog).getByRole('button', { name: /create server/i })
    await userEvent.click(submitBtn)

    await waitFor(() => {
      expect(capturedPayload).toMatchObject({
        name: 'kea-dhcp-1',
        dhcpv4_enabled: true,
        dhcpv6_enabled: false,
        ha_enabled: false,
        ha_mode: 'hot-standby',
      })
      expect(capturedPayload).not.toHaveProperty('ha_peer_address')
    })
  })

  /* ── 7. No instance → instance-notice Card ───────────────────────────── */
  it('shows instance-notice when no instance is selected', () => {
    useInstanceStore.setState({ selectedInstanceId: null })
    renderDHCP()
    expect(
      screen.getByText(/select an instance from the top bar to manage its dhcp servers/i),
    ).toBeInTheDocument()
  })

  /* ── 8. Leases search filters rows ───────────────────────────────────── */
  it('leases search filters rows', async () => {
    renderDHCP()
    await selectFirstSubnet()
    await screen.findByText('192.168.1.101')

    expect(screen.getByText('192.168.1.102')).toBeInTheDocument()

    const searchInput = screen.getByPlaceholderText('Search leases…')
    await userEvent.type(searchInput, '102')

    await waitFor(() => {
      expect(screen.queryByText('192.168.1.101')).not.toBeInTheDocument()
    })
    expect(screen.getByText('192.168.1.102')).toBeInTheDocument()
  })
})
