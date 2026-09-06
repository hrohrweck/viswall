import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { describe, it, expect, beforeEach } from 'vitest'
import { Sidebar } from '../components/Sidebar'
import { useAuthStore } from '../stores/auth'
import { useSidebarStore } from '../stores/sidebar'
import { UserRole, AuthBackend } from '../types'

// Stub matchMedia for jsdom (Toaster/Tooltip provider reads it).
if (!window.matchMedia) {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: () => ({ matches: false, addListener: () => {}, removeListener: () => {}, addEventListener: () => {}, removeEventListener: () => {}, dispatchEvent: () => false }),
  })
}

function renderAt(path: string) {
  const router = createMemoryRouter(
    [{ path: '*', element: <Sidebar /> }],
    { initialEntries: [path] },
  )
  return render(<RouterProvider router={router} />)
}

const adminUser = {
  id: 1,
  username: 'admin',
  email: 'admin@viswall.test',
  auth_backend: AuthBackend.LOCAL,
  role: UserRole.SUPERADMIN,
  is_active: true,
  instances: [1],
  preferences: {},
  last_login: null,
  created_at: '2026-01-05T12:00:00.000Z',
  updated_at: '2026-01-05T12:00:00.000Z',
}

const regularUser = {
  ...adminUser,
  id: 2,
  username: 'operator',
  email: 'operator@viswall.test',
  role: UserRole.USER,
}

describe('Sidebar', () => {
  beforeEach(() => {
    useSidebarStore.setState({ collapsed: false })
  })

  it('renders all 4 group labels', () => {
    useAuthStore.setState({ token: 'test', user: adminUser })
    renderAt('/')
    const nav = screen.getByRole('navigation')
    expect(within(nav).getByText('Overview')).toBeInTheDocument()
    expect(within(nav).getByText('Network')).toBeInTheDocument()
    expect(within(nav).getByText('Services')).toBeInTheDocument()
    expect(within(nav).getByText('Administration')).toBeInTheDocument()
  })

  it('renders all base nav items', () => {
    useAuthStore.setState({ token: 'test', user: adminUser })
    renderAt('/')
    const nav = screen.getByRole('navigation')
    const expectedLabels = [
      'Dashboard', 'Instances', 'Metrics',
      'Firewall', 'NAT Rules', 'Routing', 'Traffic Shaping', 'VPN',
      'DNS', 'DHCP', 'Mail',
      'Users', 'Audit Logs', 'LLM Providers', 'Settings',
    ]
    for (const label of expectedLabels) {
      expect(within(nav).getByText(label)).toBeInTheDocument()
    }
  })

  it('applies aria-current="page" and active class to the current route', () => {
    useAuthStore.setState({ token: 'test', user: adminUser })
    renderAt('/instances')
    const link = screen.getByRole('link', { name: 'Instances' })
    expect(link).toHaveAttribute('aria-current', 'page')
    expect(link.className).toContain('bg-primary-subtle')
    expect(link.className).toContain('text-primary')
  })

  it('hides Audit Logs and LLM Providers for non-admin users', () => {
    useAuthStore.setState({ token: 'test', user: regularUser })
    renderAt('/')
    const nav = screen.getByRole('navigation')
    expect(within(nav).queryByText('Audit Logs')).not.toBeInTheDocument()
    expect(within(nav).queryByText('LLM Providers')).not.toBeInTheDocument()
  })

  it('shows Audit Logs and LLM Providers for admin users', () => {
    useAuthStore.setState({ token: 'test', user: adminUser })
    renderAt('/')
    const nav = screen.getByRole('navigation')
    expect(within(nav).getByText('Audit Logs')).toBeInTheDocument()
    expect(within(nav).getByText('LLM Providers')).toBeInTheDocument()
  })

  it('renders collapsed rail when store is collapsed — icons only, no text labels, group labels hidden', () => {
    useAuthStore.setState({ token: 'test', user: adminUser })
    useSidebarStore.setState({ collapsed: true })
    renderAt('/')
    const nav = screen.getByRole('navigation')
    // Group labels hidden
    expect(within(nav).queryByText('Overview')).not.toBeInTheDocument()
    expect(within(nav).queryByText('Network')).not.toBeInTheDocument()
    // Text labels hidden
    expect(within(nav).queryByText('Dashboard')).not.toBeInTheDocument()
    expect(within(nav).queryByText('Instances')).not.toBeInTheDocument()
    // Icons still visible (SVGs in links)
    const links = within(nav).getAllByRole('link')
    expect(links.length).toBeGreaterThanOrEqual(10)
    // Tooltip wrappers present — collapse toggle still visible
    expect(screen.getByRole('button', { name: 'Expand sidebar' })).toBeInTheDocument()
  })

  it('collapse toggle flips the store', async () => {
    useAuthStore.setState({ token: 'test', user: adminUser })
    useSidebarStore.setState({ collapsed: false })
    renderAt('/')

    const toggle = screen.getByRole('button', { name: 'Collapse sidebar' })
    expect(toggle).toBeInTheDocument()

    const user = userEvent.setup()
    await user.click(toggle)

    expect(useSidebarStore.getState().collapsed).toBe(true)
  })

  it('Firewall sub-items are indented and carry Preview badge', () => {
    useAuthStore.setState({ token: 'test', user: adminUser })
    renderAt('/')
    const nav = screen.getByRole('navigation')
    const simLink = within(nav).getByText('Simulator').closest('a')
    const testLink = within(nav).getByText('Test Suite').closest('a')
    expect(simLink?.className).toContain('pl-8')
    expect(testLink?.className).toContain('pl-8')
    expect(within(nav).getAllByText('Preview').length).toBeGreaterThanOrEqual(2)
  })
})
