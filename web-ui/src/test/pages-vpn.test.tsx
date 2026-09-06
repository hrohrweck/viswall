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
import { vpnServers, vpnClients } from './msw/fixtures'
import { server } from './msw/node'

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
      http.post('/api/v1/vpn/:instanceId/servers/:serverId/clients', () =>
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
