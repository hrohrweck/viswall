import { beforeAll, afterAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { http, HttpResponse } from 'msw'

import { DNSServers } from '../pages/DNS/DNSServers'
import { useInstanceStore } from '../stores/instance'
import { useAuthStore } from '../stores/auth'
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
    // The page gates mutation surfaces on the admin role; the scenarios below
    // exercise those flows, so act as an admin (see pages-interfaces.test.tsx).
    useAuthStore.setState({
      token: 'test-token',
      user: { id: 1, username: 'admin', email: 'admin@example.com', role: 'superadmin' },
    })
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

    // Open the Create Record modal via the Zone Entries card's Add action.
    const entriesHeader = screen
      .getByRole('heading', { name: /Zone Entries/ })
      .closest('div') as HTMLElement
    await user.click(within(entriesHeader).getByRole('button', { name: 'Add' }))
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

/* -------------------------------------------------------------------------- */
/*  Zone entries interactive layer — selection, edit, bulk actions (todo 7)   */
/* -------------------------------------------------------------------------- */

describe('DNS zone entries — edit, selection and bulk actions', () => {
  beforeEach(() => {
    useInstanceStore.setState({ selectedInstanceId: 1 })
    useAuthStore.setState({
      token: 'test-token',
      user: { id: 1, username: 'admin', email: 'admin@example.com', role: 'superadmin' },
    })
  })

  /** Render the page and navigate to the entries table of fixture zone example.test. */
  async function openZoneEntries() {
    renderDNS()
    await screen.findByText('bind-primary')
    await userEvent.click(screen.getByText('bind-primary'))
    await screen.findByText('example.test')
    await userEvent.click(screen.getByText('example.test'))
    await waitFor(() => {
      expect(screen.getByText('192.168.1.10')).toBeInTheDocument()
    })
  }

  /** Click the selection checkbox of the table row containing `cellText`. */
  async function selectRowByContent(cellText: string) {
    const row = screen.getByText(cellText).closest('tr') as HTMLElement
    await userEvent.click(within(row).getByRole('checkbox'))
  }

  /* ── (a) Edit flow seeds the modal and PATCHes the row ──────────────── */
  it('edit flow: pencil seeds the modal and PATCHes the record', async () => {
    let capturedPatch: Record<string, unknown> | null = null
    server.use(
      http.patch('*/dns/records/:id', async ({ request }) => {
        const body = (await request.json()) as Record<string, unknown>
        capturedPatch = body
        return HttpResponse.json({
          id: 2,
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
          created_by: 1,
          created_at: '2026-01-05T12:00:00.000Z',
          updated_at: '2026-01-05T12:00:00.000Z',
        })
      }),
    )

    await openZoneEntries()

    const wwwRow = screen.getByText('192.168.1.10').closest('tr') as HTMLElement
    await userEvent.click(within(wwwRow).getByRole('button', { name: /edit record/i }))

    const dialog = await screen.findByRole('dialog')
    expect(within(dialog).getByText('Edit Record')).toBeInTheDocument()
    expect(within(dialog).getByRole('textbox', { name: 'Name' })).toHaveValue('www')
    expect(within(dialog).getByRole('combobox', { name: 'Type' })).toHaveValue('A')
    expect(within(dialog).getByRole('textbox', { name: 'Content' })).toHaveValue('192.168.1.10')
    expect(within(dialog).getByRole('spinbutton', { name: 'TTL' })).toHaveValue(300)

    await userEvent.clear(within(dialog).getByRole('textbox', { name: 'Content' }))
    await userEvent.type(within(dialog).getByRole('textbox', { name: 'Content' }), '192.168.1.20')
    await userEvent.click(within(dialog).getByRole('button', { name: /save changes/i }))

    await waitFor(() => {
      expect(capturedPatch).toEqual({
        name: 'www',
        record_type: 'A',
        content: '192.168.1.20',
        ttl: 300,
      })
    })
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })
  })

  /* ── (a2) Edit mode blocks a full-FQDN name client-side ─────────────── */
  it('edit mode rejects a full-FQDN name without firing PATCH', async () => {
    let patchCalled = false
    server.use(
      http.patch('*/dns/records/:id', async () => {
        patchCalled = true
        return HttpResponse.json({})
      }),
    )

    await openZoneEntries()

    const wwwRow = screen.getByText('192.168.1.10').closest('tr') as HTMLElement
    await userEvent.click(within(wwwRow).getByRole('button', { name: /edit record/i }))

    const dialog = await screen.findByRole('dialog')
    const nameInput = within(dialog).getByRole('textbox', { name: 'Name' })
    await userEvent.clear(nameInput)
    await userEvent.type(nameInput, 'www.example.test')
    await userEvent.click(within(dialog).getByRole('button', { name: /save changes/i }))

    // The zod guard flags the name; nothing reaches the wire.
    await waitFor(() => {
      expect(within(dialog).getByText(/relative to the zone/i)).toBeInTheDocument()
    })
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(patchCalled).toBe(false)
  })

  /* ── (b) Bulk edit applies TTL to exactly the selected ids ──────────── */
  it('bulk edit PATCHes TTL for the selected record ids', async () => {
    let capturedBulk: Record<string, unknown> | null = null
    server.use(
      http.patch('*/dns/zones/:zoneId/records/bulk', async ({ request }) => {
        capturedBulk = (await request.json()) as Record<string, unknown>
        return HttpResponse.json([])
      }),
    )

    await openZoneEntries()
    await selectRowByContent('192.168.1.10')
    await selectRowByContent('fd00:42::10')

    expect(screen.getByText('2 selected')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: /edit selected/i }))

    const dialog = await screen.findByRole('dialog')
    expect(within(dialog).getByText('Bulk Edit — 2 records')).toBeInTheDocument()
    expect(within(dialog).getByText(/Applied to all 2 selected records/)).toBeInTheDocument()

    const ttlInput = within(dialog).getByRole('spinbutton')
    await userEvent.clear(ttlInput)
    await userEvent.type(ttlInput, '600')
    await userEvent.click(within(dialog).getByRole('button', { name: /apply to 2 records/i }))

    await waitFor(() => {
      expect(capturedBulk).toEqual({ record_ids: [2, 5], changes: { ttl: 600 } })
    })
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
      expect(screen.queryByText('2 selected')).not.toBeInTheDocument()
    })
  })

  /* ── (c) Bulk delete confirms then DELETEs the selected ids ─────────── */
  it('bulk delete confirms and DELETEs the selected record ids', async () => {
    let capturedDelete: Record<string, unknown> | null = null
    server.use(
      http.delete('*/dns/zones/:zoneId/records/bulk', async ({ request }) => {
        capturedDelete = (await request.json()) as Record<string, unknown>
        return HttpResponse.json({ deleted_count: 2, record_ids: [2, 5] })
      }),
    )

    await openZoneEntries()
    await selectRowByContent('192.168.1.10')
    await selectRowByContent('fd00:42::10')

    await userEvent.click(screen.getByRole('button', { name: /delete selected/i }))

    const dialog = await screen.findByRole('dialog')
    // The title string doubles as the confirm button label — presence check.
    expect(within(dialog).getAllByText('Delete 2 Records').length).toBeGreaterThanOrEqual(1)
    expect(
      within(dialog).getByText('Delete 2 selected records from example.test?'),
    ).toBeInTheDocument()
    expect(
      within(dialog).getByText(/pushes the new zone configuration/),
    ).toBeInTheDocument()

    await userEvent.click(within(dialog).getByRole('button', { name: /delete 2 records/i }))

    await waitFor(() => {
      expect(capturedDelete).toEqual({ record_ids: [2, 5] })
    })
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
      expect(screen.queryByText('2 selected')).not.toBeInTheDocument()
    })
  })

  /* ── (d) System rows have no checkbox and no actions ────────────────── */
  it('system rows render no checkbox and no action buttons', async () => {
    await openZoneEntries()

    const systemRow = screen.getByText('192.168.1.1').closest('tr') as HTMLElement
    expect(within(systemRow).queryByRole('checkbox')).not.toBeInTheDocument()
    expect(within(systemRow).queryAllByRole('button')).toHaveLength(0)
    expect(within(systemRow).getByText('system')).toBeInTheDocument()
    expect(screen.getByRole('checkbox', { name: 'Select all records' })).toBeInTheDocument()
  })

  /* ── (e) Filters narrow rows and select-all respects the filter ─────── */
  it('filters narrow rows and select-all only picks filtered non-system rows', async () => {
    await openZoneEntries()

    const filterInput = screen.getByPlaceholderText('Filter entries…')
    await userEvent.type(filterInput, 'api')
    await userEvent.selectOptions(
      screen.getByRole('combobox', { name: 'Filter by record type' }),
      'AAAA',
    )

    await waitFor(() => {
      expect(screen.queryByText('192.168.1.10')).not.toBeInTheDocument()
    })
    expect(screen.getByText('fd00:42::10')).toBeInTheDocument()

    // Select-all with the filter active selects only the visible non-system row.
    await userEvent.click(screen.getByRole('checkbox', { name: 'Select all records' }))
    const apiRow = screen.getByText('fd00:42::10').closest('tr') as HTMLElement
    expect(within(apiRow).getByRole('checkbox')).toBeChecked()
    expect(screen.getByText('1 selected')).toBeInTheDocument()

    // Clearing the filters brings the other rows back — still unselected.
    await userEvent.clear(filterInput)
    await userEvent.selectOptions(
      screen.getByRole('combobox', { name: 'Filter by record type' }),
      '',
    )
    await waitFor(() => {
      expect(screen.getByText('192.168.1.10')).toBeInTheDocument()
    })
    const wwwRow = screen.getByText('192.168.1.10').closest('tr') as HTMLElement
    expect(within(wwwRow).getByRole('checkbox')).not.toBeChecked()
    expect(screen.getByText('1 selected')).toBeInTheDocument()
  })

  /* ── (f) Bulk operations refetch the zones card ─────────────────────── */
  it('zones query refetches after a bulk update', async () => {
    let zonesFetches = 0
    server.use(
      http.get('*/dns/servers/:serverId/zones', () => {
        zonesFetches += 1
        return HttpResponse.json(dnsZones)
      }),
      http.patch('*/dns/zones/:zoneId/records/bulk', () => HttpResponse.json([])),
    )

    await openZoneEntries()
    expect(zonesFetches).toBe(1)

    await selectRowByContent('192.168.1.10')
    await userEvent.click(screen.getByRole('button', { name: /edit selected/i }))
    const dialog = await screen.findByRole('dialog')
    const ttlInput = within(dialog).getByRole('spinbutton')
    await userEvent.clear(ttlInput)
    await userEvent.type(ttlInput, '600')
    await userEvent.click(within(dialog).getByRole('button', { name: /apply to 1 records/i }))

    await waitFor(() => {
      expect(zonesFetches).toBeGreaterThanOrEqual(2)
    })
  })

  /* ── (g) Non-admin sees the table but no mutation surfaces ──────────── */
  it('non-admin sees the table without checkboxes, pencil or bulk toolbar', async () => {
    useAuthStore.setState({
      token: 'test-token',
      user: { id: 2, username: 'viewer', email: 'viewer@example.com', role: 'readonly' },
    })

    await openZoneEntries()

    expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /edit record/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /delete record/i })).not.toBeInTheDocument()
    expect(screen.queryByText(/selected/)).not.toBeInTheDocument()
    expect(screen.getByText('192.168.1.10')).toBeInTheDocument()
    expect(screen.getByText('system')).toBeInTheDocument()
  })
})
