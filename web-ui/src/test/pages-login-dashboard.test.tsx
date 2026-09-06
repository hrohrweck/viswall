import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { http, HttpResponse } from 'msw'
import { Login } from '../pages/Login'
import { Dashboard } from '../pages/Dashboard'
import { useAuthStore } from '../stores/auth'
import {
  loginResponse,
  validCredentials,
  instances,
  metricsOverview,
} from './msw/fixtures'
import { server } from './msw/node'
import userEvent from '@testing-library/user-event'

/* -------------------------------------------------------------------------- */
/*  Helpers                                                                    */
/* -------------------------------------------------------------------------- */

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
}

function renderLogin() {
  const qc = makeQueryClient()
  const utils = render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <Login />
      </MemoryRouter>
    </QueryClientProvider>,
  )
  return { ...utils, qc }
}

function renderDashboard() {
  const qc = makeQueryClient()
  const utils = render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/']}>
        <Dashboard />
      </MemoryRouter>
    </QueryClientProvider>,
  )
  return { ...utils, qc }
}

/* -------------------------------------------------------------------------- */
/*  Login tests                                                                */
/* -------------------------------------------------------------------------- */

describe('Login page', () => {
  beforeEach(() => {
    localStorage.clear()
    useAuthStore.setState({ token: null, user: null })
  })

  it('renders sign-in form with Field/Label wiring and uses useLogin hook', () => {
    renderLogin()

    // Heading
    expect(screen.getByRole('heading', { name: 'Sign in' })).toBeInTheDocument()

    // Labels are associated via Field + htmlFor
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()

    // Password field has correct type
    expect(screen.getByLabelText(/password/i)).toHaveAttribute('type', 'password')

    // Submit button
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()

    // "Stay signed in" checkbox
    expect(screen.getByLabelText(/stay signed in/i)).toBeInTheDocument()
  })

  it('logs in successfully — sets auth store via useLogin + MSW', async () => {
    const user = userEvent.setup()
    renderLogin()

    await user.type(screen.getByLabelText(/username/i), validCredentials.username)
    await user.type(screen.getByLabelText(/password/i), validCredentials.password)
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(useAuthStore.getState().token).toBe(loginResponse.access_token)
    })

    expect(useAuthStore.getState().user?.username).toBe(loginResponse.user.username)
  })

  it('shows error banner on failed login with danger-subtle bg', async () => {
    // Truthful since the interceptor /auth/ guard: a failed login must NOT
    // clear session storage (the old false-green relied on jsdom ignoring
    // the location redirect — removeItem still fired there).
    const removeItemSpy = vi.spyOn(Storage.prototype, 'removeItem')

    const user = userEvent.setup()
    renderLogin()

    await user.type(screen.getByLabelText(/username/i), 'admin')
    await user.type(screen.getByLabelText(/password/i), 'wrong-password')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    const banner = await screen.findByRole('alert')
    expect(banner).toHaveTextContent('Invalid credentials')

    // Token classes on the banner
    expect(banner.className).toContain('bg-danger-subtle')
    expect(banner.className).toContain('text-danger')

    // Auth store stays empty
    expect(useAuthStore.getState().token).toBeNull()

    // The 401 interceptor skipped the /auth/ request: no session clear,
    // and the Login page stayed mounted (no redirect/unmount in jsdom).
    expect(removeItemSpy).not.toHaveBeenCalled()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()

    removeItemSpy.mockRestore()
  })
})

/* -------------------------------------------------------------------------- */
/*  Dashboard tests                                                            */
/* -------------------------------------------------------------------------- */

describe('Dashboard page', () => {
  it('renders4 stat cards with static status classes', async () => {
    renderDashboard()

    // Wait for data to load — the value text replaces the Skeleton
    await waitFor(() => {
      expect(screen.getAllByText(String(metricsOverview.instances)).length).toBeGreaterThanOrEqual(1)
    })

    // Assert stat card labels
    expect(screen.getByText('Total instances')).toBeInTheDocument()
    expect(screen.getByText('Firewall rules')).toBeInTheDocument()
    expect(screen.getByText('VPN servers')).toBeInTheDocument()
    expect(screen.getByText('Mail domains')).toBeInTheDocument()

    // Verify static token classes on icon containers
    const primaryIcon = screen.getByText('Total instances')
      .closest('a')!
      .querySelector('.bg-primary-subtle')
    expect(primaryIcon).toBeInTheDocument()

    const successIcon = screen.getByText('Firewall rules')
      .closest('a')!
      .querySelector('.bg-success-subtle')
    expect(successIcon).toBeInTheDocument()
  })

  it('renders instance health table with rows from fixtures', async () => {
    renderDashboard()

    // Wait for table data to load — use findByText for the first instance
    await screen.findByText('edge-berlin-01')

    // All three instances are rendered in the table (first occurrence is table)
    expect(screen.getAllByText('edge-berlin-01').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('edge-oslo-02').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('edge-vie-03').length).toBeGreaterThanOrEqual(1)

    // Hostnames in table
    expect(screen.getByText('berlin.edge.viswall.test')).toBeInTheDocument()

    // Status badges rendered — "maintenance" also appears in attention card, use getAllByText
    expect(screen.getAllByText('active').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('maintenance').length).toBeGreaterThanOrEqual(1)
  })

  it('shows "All systems nominal" when no instances need attention', async () => {
    // Override to return only active instance
    server.use(
      http.get('/api/v1/instances', () => HttpResponse.json([instances[0]])),
    )

    renderDashboard()

    await waitFor(() => {
      expect(screen.getByText('All systems nominal')).toBeInTheDocument()
    })
  })

  it('shows attention instances with View buttons', async () => {
    renderDashboard()

    // Wait for instances to load in the table first
    await screen.findByText('edge-berlin-01')

    // The attention card should now have maintenance/offline instances
    // Find the "Attention needed" heading
    const heading = screen.getByText('Attention needed')
    // Navigate up to the Card (rounded-card container)
    const card = heading.closest('.rounded-card')!
    const cardBody = card.querySelector('.p-5')!

    // edge-oslo-02 (maintenance) should be in the attention card
    expect(cardBody.textContent).toContain('edge-oslo-02')
    // edge-vie-03 (offline) should be in the attention card
    expect(cardBody.textContent).toContain('edge-vie-03')
  })
})
