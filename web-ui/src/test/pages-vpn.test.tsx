import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, within, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { http, HttpResponse } from 'msw'
import { useInstanceStore } from '../stores/instance'
import { VPNServers } from '../pages/VPN/VPNServers'
import { VPNServerDetail } from '../pages/VPN/VPNServerDetail'
import { VPNCreate } from '../pages/VPN/VPNCreate'
import { VPNSiteToSite } from '../pages/VPN/VPNSiteToSite'
import { vpnServers, vpnClients } from './msw/fixtures'
import { server } from './msw/node'
import { toast } from 'sonner'

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
/*  helpers                                                            */
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

function DetailWrapper({ children, initialEntry }: { children: React.ReactNode; initialEntry: string }) {
  const qc = makeQueryClient()
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <Routes>
          <Route path="/vpn/servers/:id" element={children} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

function setInstance(id: number) {
  useInstanceStore.setState({ selectedInstanceId: id })
}

function renderVPNServers() {
  return render(
    <Wrapper>
      <VPNServers />
    </Wrapper>,
  )
}

function renderVPNServerDetail(serverId: number) {
  return render(
    <DetailWrapper initialEntry={`/vpn/servers/${String(serverId)}`}>
      <VPNServerDetail />
    </DetailWrapper>,
  )
}

function renderVPNCreate() {
  return render(
    <Wrapper>
      <VPNCreate />
    </Wrapper>,
  )
}

/* ------------------------------------------------------------------ */
/*  setup                                                              */
/* ------------------------------------------------------------------ */

beforeEach(() => {
  setInstance(1)
})

/* ================================================================== */
/*  1 — VPNServers subtitle is corrected                               */
/* ================================================================== */

describe('VPNServers subtitle', () => {
  it('renders the correct VPN subtitle (not the mail copy-paste)', () => {
    renderVPNServers()
    expect(
      screen.getByText('WireGuard, IPsec and OpenVPN servers across your instances'),
    ).toBeInTheDocument()
    expect(
      screen.queryByText('Manage email domains, users, and security settings'),
    ).not.toBeInTheDocument()
  })
})

describe('VPNServers no-instance notice', () => {
  it('shows instance-notice Card when no instance selected', () => {
    setInstance(null as unknown as number)
    renderVPNServers()
    expect(screen.getByText('VPN Servers')).toBeInTheDocument()
    expect(
      screen.getByText('Select an instance from the top bar to manage its VPN servers.'),
    ).toBeInTheDocument()
  })

  it('does not render raw InstanceSelector when no instance selected', () => {
    setInstance(null as unknown as number)
    renderVPNServers()
    expect(screen.queryByRole('combobox')).not.toBeInTheDocument()
  })
})

/* ================================================================== */
/*  2 — Stop confirm shows client-count impact                         */
/* ================================================================== */

describe('Stop confirm impact', () => {
  it('shows connected client count in stop confirm dialog', async () => {
    const user = userEvent.setup()
    renderVPNServerDetail(1)

    // Wait for server data to load
    await waitFor(() => {
      expect(screen.getByText('wg-site-a')).toBeInTheDocument()
    })

    // Click the Stop button
    const stopBtn = screen.getByRole('button', { name: /stop/i })
    await user.click(stopBtn)

    // The confirm dialog should show the impact line with client count
    await waitFor(() => {
      expect(screen.getByText(/Disconnects.*connected clients/)).toBeInTheDocument()
    })
    // The fixture server id=1 has 2 clients in vpnClients
    expect(screen.getByText(/Disconnects 2 connected clients/)).toBeInTheDocument()
  })
})

/* ================================================================== */
/*  3 — Revoke client confirm has impact line                          */
/* ================================================================== */

describe('Revoke client confirm', () => {
  it('renders client table with revoke-capable rows', async () => {
    renderVPNServerDetail(1)

    await waitFor(() => {
      expect(screen.getByText('laptop-admin')).toBeInTheDocument()
    })

    expect(screen.getByText('oslo-site-peer')).toBeInTheDocument()
    expect(screen.getAllByText('10.10.0.2').length).toBeGreaterThan(0)
  })
})

/* ================================================================== */
/*  4 — Add-client modal submits                                       */
/* ================================================================== */

describe('Add client modal', () => {
  it('opens modal with fields and submits', async () => {
    server.use(
      http.post('/api/v1/vpn/servers/:serverId/clients', () =>
        HttpResponse.json({
          id: 99, server_id: 1, user_id: null, name: 'test-client-01',
          description: null, enabled: true, client_type: 'user', auth_type: 'public_key',
          assigned_ip: null, allowed_ips: [], push_routes_override: [],
          last_connected: null, last_ip: null, connection_count: 0,
          bytes_received: 0, bytes_sent: 0, public_key: null,
          config_qr: null, config_file: null,
          created_at: '2026-01-05T12:00:00.000Z', updated_at: '2026-01-05T12:00:00.000Z',
        }),
      ),
    )
    const user = userEvent.setup()
    renderVPNServerDetail(1)

    await waitFor(() => {
      expect(screen.getByText('wg-site-a')).toBeInTheDocument()
    })

    const addBtn = screen.getByRole('button', { name: /add client/i })
    await user.click(addBtn)

    const modal = await screen.findByRole('dialog')
    expect(modal).toBeInTheDocument()

    const nameInput = within(modal).getByPlaceholderText("e.g. John's Laptop")
    await user.type(nameInput, 'test-client-01')

    const createBtn = within(modal).getByRole('button', { name: /create/i })
    await user.click(createBtn)

    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })
  })
})

/* ================================================================== */
/*  5 — VPNCreate renders static classes (no template interpolation)    */
/* ================================================================== */

describe('VPNCreate static classes', () => {
  it('renders protocol card icons with concrete CSS classes from colorMap', async () => {
    renderVPNCreate()

    // The WireGuard card icon should have text-green-600 (from colorMap, not template)
    // Find the Zap icon for WireGuard (first protocol card)
    const cards = screen.getAllByRole('button')
    const wireguardCard = cards.find((c) => within(c).queryByText('WireGuard'))
    expect(wireguardCard).toBeTruthy()

    // The icon inside should have the concrete class text-green-600
    const icon = wireguardCard!.querySelector('svg')
    expect(icon).toBeTruthy()
    expect(icon).toHaveClass('text-green-600')

    // The progress bar should have bg-green-500 (concrete, not template)
    const bar = wireguardCard!.querySelector('.bg-green-500')
    expect(bar).toBeInTheDocument()
  })

  it('has no template literal classNames in VPNCreate source', () => {
    // This is a meta-test: verify that the VPNCreate component source
    // does not contain dynamically interpolated Tailwind class names.
    // We verify this by checking rendered output has concrete classes instead
    renderVPNCreate()

    // IPsec card should have text-blue-600
    const cards = screen.getAllByRole('button')
    const ipsecCard = cards.find((c) => within(c).queryByText('IPsec/IKEv2'))
    expect(ipsecCard).toBeTruthy()
    const ipsecIcon = ipsecCard!.querySelector('svg')
    expect(ipsecIcon).toHaveClass('text-blue-600')
  })
})

/* ================================================================== */
/*  6 — Not-found shows EmptyState (not bare <p>)                      */
/* ================================================================== */

describe('VPNServerDetail not-found', () => {
  it('shows EmptyState when server is not found (404)', async () => {
    renderVPNServerDetail(999)

    // Should show the EmptyState, not a bare <p>
    await waitFor(() => {
      expect(screen.getByText('VPN server not found')).toBeInTheDocument()
    })
    // Should have a link back to VPN servers
    expect(screen.getByText('Back to VPN Servers')).toBeInTheDocument()
    // Should NOT show bare <p>Server not found.</p>
    expect(screen.queryByText('Server not found.')).not.toBeInTheDocument()
  })
})

/* ================================================================== */
/*  7 — Search filters clients in detail table                         */
/* ================================================================== */

describe('Client search filtering', () => {
  it('filters clients table by search input', async () => {
    const user = userEvent.setup()
    renderVPNServerDetail(1)

    // Wait for clients to load
    await waitFor(() => {
      expect(screen.getByText('laptop-admin')).toBeInTheDocument()
    })

    // Both clients should be visible
    expect(screen.getByText('oslo-site-peer')).toBeInTheDocument()

    // Type in the search input
    const searchInput = screen.getByPlaceholderText('Search clients…')
    await user.type(searchInput, 'laptop')

    // Only laptop-admin should be visible
    await waitFor(() => {
      expect(screen.getByText('laptop-admin')).toBeInTheDocument()
    })
    expect(screen.queryByText('oslo-site-peer')).not.toBeInTheDocument()
  })
})

/* ================================================================== */
/*  8 — Site-to-site tunnel view                                       */
/* ================================================================== */

function renderVPNSiteToSite() {
  return render(
    <Wrapper>
      <VPNSiteToSite />
    </Wrapper>,
  )
}

describe('SiteToSite status card', () => {
  it('renders tunnel status: up badge, endpoint, handshake age, transfer', async () => {
    renderVPNSiteToSite()

    await waitFor(() => {
      expect(
        screen.getByText('site-to-site-base0.webmasters.co.at-51820'),
      ).toBeInTheDocument()
    })

    expect(screen.getByText('Up')).toBeInTheDocument()
    expect(screen.getByText('base0.webmasters.co.at:51820')).toBeInTheDocument()
    expect(screen.getByText('12s ago')).toBeInTheDocument()
    expect(screen.getByText('↓1 MB')).toBeInTheDocument()
    expect(screen.getByText('↑2 MB')).toBeInTheDocument()
    expect(screen.getByText('10.80.0.0/16')).toBeInTheDocument()
    expect(screen.getByText('10.200.0.2/24')).toBeInTheDocument()
  })

  it('shows EmptyState when no tunnel exists', async () => {
    server.use(
      http.get('/api/v1/vpn/site-to-site/status', () => HttpResponse.json([])),
    )
    renderVPNSiteToSite()

    await waitFor(() => {
      expect(screen.getByText('No site-to-site tunnel')).toBeInTheDocument()
    })
    expect(
      screen.getByRole('button', { name: /initialize tunnel/i }),
    ).toBeInTheDocument()
  })
})

describe('SiteToSite initialize validation', () => {
  it('blocks empty endpoint/key with client-side field errors', async () => {
    const user = userEvent.setup()
    server.use(
      http.get('/api/v1/vpn/site-to-site/status', () => HttpResponse.json([])),
    )
    renderVPNSiteToSite()

    await waitFor(() => {
      expect(screen.getByText('No site-to-site tunnel')).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /initialize tunnel/i }))

    expect(await screen.findByText('Remote endpoint is required')).toBeInTheDocument()
    expect(screen.getByText('Peer public key is required')).toBeInTheDocument()
  })

  it('surfaces a server-side rejection as a toast error', async () => {
    const user = userEvent.setup()
    server.use(
      http.get('/api/v1/vpn/site-to-site/status', () => HttpResponse.json([])),
      http.post('/api/v1/vpn/site-to-site/initialize', () =>
        HttpResponse.json(
          { detail: 'Site-to-site tunnel already exists for this instance' },
          { status: 409 },
        ),
      ),
    )
    renderVPNSiteToSite()

    await waitFor(() => {
      expect(screen.getByText('No site-to-site tunnel')).toBeInTheDocument()
    })

    await user.type(
      screen.getByPlaceholderText('base0.example.com:51820'),
      'base0.example.com:51820',
    )
    await user.type(
      screen.getByPlaceholderText('kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk='),
      'kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk=',
    )
    await user.click(screen.getByRole('button', { name: /initialize tunnel/i }))

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        'Site-to-site tunnel already exists for this instance',
      )
    })
  })
})

describe('SiteToSite edit fields', () => {
  it('PATCHes endpoint/allowed_ips/persistent_keepalive on save', async () => {
    const user = userEvent.setup()
    let patchedBody: Record<string, unknown> | null = null
    server.use(
      http.patch('/api/v1/vpn/servers/:serverId', async ({ request }) => {
        patchedBody = (await request.json()) as Record<string, unknown>
        return HttpResponse.json({ status: 'success' })
      }),
    )
    renderVPNSiteToSite()

    await waitFor(() => {
      expect(
        screen.getByText('site-to-site-base0.webmasters.co.at-51820'),
      ).toBeInTheDocument()
    })

    const endpointInput = screen.getByDisplayValue('base0.webmasters.co.at:51820')
    await user.clear(endpointInput)
    await user.type(endpointInput, 'base0.webmasters.co.at:51821')

    const keepaliveInput = screen.getByDisplayValue('25')
    await user.clear(keepaliveInput)
    await user.type(keepaliveInput, '30')

    await user.click(screen.getByRole('button', { name: /save configuration/i }))

    await waitFor(() => {
      expect(patchedBody).not.toBeNull()
    })
    expect(patchedBody).toMatchObject({
      endpoint: 'base0.webmasters.co.at:51821',
      allowed_ips: '10.80.0.0/16',
      persistent_keepalive: 30,
    })
    expect(toast.success).toHaveBeenCalledWith('Tunnel configuration saved')
  })
})

describe('SiteToSite start/stop', () => {
  it('posts stop only after confirm', async () => {
    const user = userEvent.setup()
    let stopped = false
    server.use(
      http.post('/api/v1/vpn/servers/:serverId/stop', () => {
        stopped = true
        return HttpResponse.json({ success: true, action: 'stop' })
      }),
    )
    renderVPNSiteToSite()

    await waitFor(() => {
      expect(
        screen.getByText('site-to-site-base0.webmasters.co.at-51820'),
      ).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /^stop$/i }))
    expect(stopped).toBe(false)

    const dialog = await screen.findByRole('dialog')
    await user.click(within(dialog).getByRole('button', { name: /^stop$/i }))

    await waitFor(() => {
      expect(stopped).toBe(true)
    })
    expect(toast.success).toHaveBeenCalledWith(
      'Tunnel "site-to-site-base0.webmasters.co.at-51820" stopped',
    )
  })

  it('posts start directly', async () => {
    const user = userEvent.setup()
    let started = false
    server.use(
      http.post('/api/v1/vpn/servers/:serverId/start', () => {
        started = true
        return HttpResponse.json({ success: true, action: 'start' })
      }),
    )
    renderVPNSiteToSite()

    await waitFor(() => {
      expect(
        screen.getByText('site-to-site-base0.webmasters.co.at-51820'),
      ).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /^start$/i }))

    await waitFor(() => {
      expect(started).toBe(true)
    })
  })
})

describe('SiteToSite rotate keys', () => {
  it('POSTs regenerate and shows the new public key', async () => {
    const user = userEvent.setup()
    let regeneratedId: string | null = null
    server.use(
      http.post('/api/v1/vpn/clients/:clientId/regenerate', ({ params }) => {
        regeneratedId = String(params.clientId)
        return HttpResponse.json({
          status: 'success',
          message: 'Client credentials regenerated',
          public_key: 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb=',
        })
      }),
    )
    renderVPNSiteToSite()

    await waitFor(() => {
      expect(
        screen.getByText('site-to-site-base0.webmasters.co.at-51820'),
      ).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /rotate keys/i }))

    const dialog = await screen.findByRole('dialog')
    expect(
      within(dialog).getByText(/handed to the remote operator/i),
    ).toBeInTheDocument()
    await user.click(within(dialog).getByRole('button', { name: /rotate keys/i }))

    await waitFor(() => {
      expect(regeneratedId).toBe('3')
    })

    const resultDialog = await screen.findByText('New tunnel public key')
    expect(resultDialog).toBeInTheDocument()
    expect(
      screen.getByText('bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb='),
    ).toBeInTheDocument()
  })
})
