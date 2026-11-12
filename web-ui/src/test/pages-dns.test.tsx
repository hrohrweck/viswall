import { beforeAll, afterAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { http, HttpResponse } from 'msw'

import { DNSServers } from '../pages/DNS/DNSServers'
import { useInstanceStore } from '../stores/instance'
import { server } from './msw/node'
import { dnsServers, dnsZones, dnsRecords } from './msw/fixtures'

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

function renderDNS() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <DNSServers />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

/* -------------------------------------------------------------------------- */
/*  Test suite                                                                 */
/* -------------------------------------------------------------------------- */

describe('DNS Management page', () => {
  beforeEach(() => {
    // Seed the instance store so the page renders content (not the empty state).
    useInstanceStore.setState({ selectedInstanceId: 1 })
  })

  /* ── 1. Start action opens ConfirmDialog before firing mutation ──────── */
  it('Start server opens ConfirmDialog before firing', async () => {
    const mutateSpy = vi.fn()
    server.use(
      http.post('*/dns/servers/:id/actions/start', async () => {
        mutateSpy()
        return HttpResponse.json({ status: 'started' })
      }),
    )

    renderDNS()

    // Wait for servers to load.
    await screen.findByText('bind-primary')

    // Click the Start icon button (wrapped in Tooltip → rendered as button).
    const startBtn = screen.getByRole('button', { name: /start server/i })
    await userEvent.click(startBtn)

    // ConfirmDialog should appear — the mutation must NOT have fired yet.
    const dialog = await screen.findByRole('dialog')
    expect(dialog).toBeInTheDocument()
    expect(mutateSpy).not.toHaveBeenCalled()

    // Confirm.
    const confirmBtn = within(dialog).getByRole('button', { name: /start/i })
    await userEvent.click(confirmBtn)

    await waitFor(() => expect(mutateSpy).toHaveBeenCalledTimes(1))
  })

  /* ── 2. Stop action opens ConfirmDialog before firing ───────────────── */
  it('Stop server opens ConfirmDialog before firing', async () => {
    const mutateSpy = vi.fn()
    server.use(
      http.post('*/dns/servers/:id/actions/stop', async () => {
        mutateSpy()
        return HttpResponse.json({ status: 'stopped' })
      }),
    )

    renderDNS()
    await screen.findByText('bind-primary')

    const stopBtn = screen.getByRole('button', { name: /stop server/i })
    await userEvent.click(stopBtn)

    const dialog = await screen.findByRole('dialog')
    expect(dialog).toBeInTheDocument()
    expect(mutateSpy).not.toHaveBeenCalled()

    const confirmBtn = within(dialog).getByRole('button', { name: /stop/i })
    await userEvent.click(confirmBtn)

    await waitFor(() => expect(mutateSpy).toHaveBeenCalledTimes(1))
  })

  /* ── 3. Reload action opens ConfirmDialog before firing ──────────────── */
  it('Reload server opens ConfirmDialog before firing', async () => {
    const mutateSpy = vi.fn()
    server.use(
      http.post('*/dns/servers/:id/actions/reload', async () => {
        mutateSpy()
        return HttpResponse.json({ status: 'reloaded' })
      }),
    )

    renderDNS()
    await screen.findByText('bind-primary')

    const reloadBtn = screen.getByRole('button', { name: /reload server/i })
    await userEvent.click(reloadBtn)

    const dialog = await screen.findByRole('dialog')
    expect(dialog).toBeInTheDocument()
    expect(mutateSpy).not.toHaveBeenCalled()

    const confirmBtn = within(dialog).getByRole('button', { name: /reload/i })
    await userEvent.click(confirmBtn)

    await waitFor(() => expect(mutateSpy).toHaveBeenCalledTimes(1))
  })

  /* ── 4. Selecting a zone loads the records pane ─────────────────────── */
  it('selecting a zone loads records pane', async () => {
    renderDNS()

    // Wait for servers.
    await screen.findByText('bind-primary')

    // Click the server to load zones.
    const serverBtn = screen.getByText('bind-primary')
    await userEvent.click(serverBtn)

    // Wait for zones.
    await screen.findByText('example.test')

    // Click a zone.
    const zoneBtn = screen.getByText('example.test')
    await userEvent.click(zoneBtn)

    // Records should load.
    await waitFor(() => {
      expect(screen.getByText('192.168.1.10')).toBeInTheDocument()
    })
  })

  /* ── 5. Record search filters zones list ────────────────────────────── */
  it('zone search filters the zones list', async () => {
    renderDNS()

    await screen.findByText('bind-primary')

    // Select server to load zones.
    await userEvent.click(screen.getByText('bind-primary'))
    await screen.findByText('example.test')

    // The zones pane should show both zones.
    expect(screen.getByText('example.test')).toBeInTheDocument()
    expect(screen.getByText('1.168.192.in-addr.arpa')).toBeInTheDocument()

    // Type into the zone search.
    const searchInput = screen.getByPlaceholderText('Search zones…')
    await userEvent.type(searchInput, 'example')

    // Only matching zone should remain visible.
    await waitFor(() => {
      expect(screen.getByText('example.test')).toBeInTheDocument()
      expect(screen.queryByText('1.168.192.in-addr.arpa')).not.toBeInTheDocument()
    })
  })

  /* ── 6. Create server form submits unchanged payload ────────────────── */
  it('Create Server form submits expected payload', async () => {
    let capturedPayload: Record<string, unknown> | null = null
    server.use(
      http.post('*/dns/servers/:instanceId', async ({ request }) => {
        capturedPayload = (await request.json()) as Record<string, unknown>
        return HttpResponse.json({
          id: 99,
          instance_id: 1,
          name: 'new-server',
          status: 'stopped',
          zones_count: 0,
          port: 53,
          ...capturedPayload,
        })
      }),
    )

    renderDNS()
    await screen.findByText('bind-primary')

    // Open create server modal.
    const newBtn = screen.getByRole('button', { name: /new dns server/i })
    await userEvent.click(newBtn)

    // Wait for the form to appear.
    const dialog = await screen.findByRole('dialog')

    // The default values are pre-filled. Submit as-is.
    const submitBtn = within(dialog).getByRole('button', { name: /create server/i })
    await userEvent.click(submitBtn)

    await waitFor(() => {
      expect(capturedPayload).toEqual({
        name: 'dns-server-1',
        is_recursive: true,
        is_authoritative: true,
        forwarders: ['1.1.1.1', '8.8.8.8'],
      })
    })
  })

  /* ── 7. Delete zone opens ConfirmDialog ──────────────────────────────── */
  it('Delete zone opens ConfirmDialog', async () => {
    const mutateSpy = vi.fn()
    server.use(
      http.delete('*/dns/zones/:zoneId', async () => {
        mutateSpy()
        return HttpResponse.json({ status: 'deleted' })
      }),
    )

    renderDNS()
    await screen.findByText('bind-primary')

    // Select server to load zones.
    await userEvent.click(screen.getByText('bind-primary'))
    await screen.findByText('example.test')

    // Find the delete button for the first zone.
    const deleteButtons = screen.getAllByRole('button', { name: /delete zone/i })
    await userEvent.click(deleteButtons[0])

    // ConfirmDialog should appear.
    const dialog = await screen.findByRole('dialog')
    expect(dialog).toBeInTheDocument()
    expect(mutateSpy).not.toHaveBeenCalled()

    // Confirm the delete.
    const confirmBtn = within(dialog).getByRole('button', { name: /delete/i })
    await userEvent.click(confirmBtn)

    await waitFor(() => expect(mutateSpy).toHaveBeenCalledTimes(1))
  })

  /* ── 8. No instance → compact notice ─────────────────────────────────── */
  it('shows compact notice when no instance is selected', () => {
    useInstanceStore.setState({ selectedInstanceId: null })
    renderDNS()
    expect(
      screen.getByText(/select an instance from the top bar/i),
    ).toBeInTheDocument()
  })

  /* ── 9. Create Record modal posts a DKIM TXT payload for the zone ───── */
  it('Create Record modal submits a DKIM name and TXT payload', async () => {
    const user = userEvent.setup()
    let capturedRecord: Record<string, unknown> | null = null
    server.use(
      http.post('*/dns/zones/:zoneId/records', async ({ request }) => {
        const body = (await request.json()) as Record<string, unknown>
        capturedRecord = body
        return HttpResponse.json(
          {
            id: 999,
            zone_id: 1,
            name: body.name,
            record_type: body.record_type,
            content: body.content,
            ttl: body.ttl,
            priority: 0,
            weight: 0,
            port: 0,
            flags: '',
            tag: null,
            comment: null,
            is_system: false,
            created_by: null,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          { status: 201 },
        )
      }),
    )

    renderDNS()
    await screen.findByText('bind-primary')

    // Select the server, then the fixture zone example.test.
    await user.click(screen.getByText('bind-primary'))
    await screen.findByText('example.test')
    await user.click(screen.getByText('example.test'))
    await waitFor(() => {
      expect(screen.getByText('192.168.1.10')).toBeInTheDocument()
    })

    // Open the Create Record modal via the Records card's Add action.
    const recordsHeader = screen.getByRole('heading', { name: 'Records' }).closest('div') as HTMLElement
    await user.click(within(recordsHeader).getByRole('button', { name: 'Add' }))
    const dialog = await screen.findByRole('dialog')

    // Fill the form: DKIM name, TXT type, DKIM key content. TTL keeps its 3600 default.
    const nameInput = within(dialog).getByRole('textbox', { name: 'Name' })
    await user.clear(nameInput)
    await user.type(nameInput, 'mail._domainkey')
    await user.selectOptions(within(dialog).getByRole('combobox', { name: 'Type' }), 'TXT')
    const contentInput = within(dialog).getByRole('textbox', { name: 'Content' })
    await user.clear(contentInput)
    await user.type(contentInput, 'v=DKIM1; k=rsa; p=MIIBOgIBAAJBAK8h7Q')

    await user.click(within(dialog).getByRole('button', { name: 'Create Record' }))

    // The POST body is the deliverable proof: DKIM name accepted end-to-end.
    await waitFor(() => {
      expect(capturedRecord).toEqual({
        name: 'mail._domainkey',
        record_type: 'TXT',
        content: 'v=DKIM1; k=rsa; p=MIIBOgIBAAJBAK8h7Q',
        ttl: 3600,
      })
    })

    // Success path: the modal closed again.
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })
  })
})
