import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { CommandPalette } from '../components/ui/CommandPalette'
import { useAuthStore } from '../stores/auth'
import { useInstanceStore } from '../stores/instance'
import { useCommandPaletteStore } from '../stores/commandPalette'
import { loginResponse } from './msw/fixtures'

/* ── helpers ── */

function createWrapper(initialEntries: string[] = ['/']) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return function Wrapper({ children }: { children?: ReactNode }) {
    return (
      <QueryClientProvider client={qc}>
        <MemoryRouter initialEntries={initialEntries}>
          {children}
        </MemoryRouter>
      </QueryClientProvider>
    )
  }
}

/** Reads current location — rendered as a test child for navigation assertions. */
function LocationDisplay() {
  const { pathname } = useLocation()
  return <span data-testid="location">{pathname}</span>
}

/* ── tests ── */

describe('Command palette', () => {
  let originalMatchMedia: typeof window.matchMedia
  let originalResizeObserver: typeof window.ResizeObserver

  beforeEach(() => {
    // Stub matchMedia for jsdom (theme store reads it).
    originalMatchMedia = window.matchMedia
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      configurable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    })

    // Polyfill ResizeObserver for jsdom (cmdk uses it internally).
    originalResizeObserver = window.ResizeObserver
    window.ResizeObserver = class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    }

    // Polyfill scrollIntoView for jsdom (cmdk scrolls to the selected item).
    if (!Element.prototype.scrollIntoView) {
      Element.prototype.scrollIntoView = vi.fn()
    }

    // Seed auth store as admin.
    useAuthStore.setState({
      token: loginResponse.access_token,
      user: {
        id: loginResponse.user.id,
        username: loginResponse.user.username,
        email: loginResponse.user.email,
        role: loginResponse.user.role, // superadmin
      },
    })
    useInstanceStore.setState({ selectedInstanceId: null })
    useCommandPaletteStore.setState({ open: false })
  })

  afterEach(() => {
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      configurable: true,
      value: originalMatchMedia,
    })
    window.ResizeObserver = originalResizeObserver
    useCommandPaletteStore.setState({ open: false })
    cleanup()
  })

  /* 1 ── setOpen(true) renders dialog with input */
  it('renders dialog with input when store open=true', async () => {
    useCommandPaletteStore.setState({ open: true })
    render(
      <>
        <CommandPalette />
        <LocationDisplay />
      </>,
      { wrapper: createWrapper() },
    )

    // cmdk Dialog renders via Radix Portal → waitFor.
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Search pages, instances, actions…')).toBeInTheDocument()
    })
  })

  /* 2 ── Typing 'vpn' filters — VPN visible, Dashboard hidden */
  it('typing "vpn" filters items: VPN visible, Dashboard hidden', async () => {
    const user = userEvent.setup()
    useCommandPaletteStore.setState({ open: true })
    render(
      <>
        <CommandPalette />
        <LocationDisplay />
      </>,
      { wrapper: createWrapper() },
    )

    const input = await screen.findByPlaceholderText('Search pages, instances, actions…')
    await user.type(input, 'vpn')

    // cmdk filters in real-time.
    await waitFor(() => {
      expect(screen.getByText('VPN')).toBeInTheDocument()
    })
    // Dashboard should be filtered out.
    expect(screen.queryByText('Dashboard')).not.toBeInTheDocument()
  })

  /* 3 ── Enter on first match navigates and closes */
  it('Enter on first match navigates to /vpn and closes the palette', async () => {
    const user = userEvent.setup()
    useCommandPaletteStore.setState({ open: true })
    render(
      <>
        <CommandPalette />
        <LocationDisplay />
      </>,
      { wrapper: createWrapper() },
    )

    const input = await screen.findByPlaceholderText('Search pages, instances, actions…')
    await user.type(input, 'vpn')

    // Wait for VPN item to appear.
    await waitFor(() => {
      expect(screen.getByText('VPN')).toBeInTheDocument()
    })

    // Press Enter to select the first match.
    await user.keyboard('{Enter}')

    // Navigation: location should be /vpn.
    await waitFor(() => {
      expect(screen.getByTestId('location')).toHaveTextContent('/vpn')
    })

    // Palette should be closed.
    await waitFor(() => {
      expect(useCommandPaletteStore.getState().open).toBe(false)
    })
  })

  /* 4 ── Escape closes */
  it('Escape closes the palette', async () => {
    const user = userEvent.setup()
    useCommandPaletteStore.setState({ open: true })
    render(
      <>
        <CommandPalette />
        <LocationDisplay />
      </>,
      { wrapper: createWrapper() },
    )

    await screen.findByPlaceholderText('Search pages, instances, actions…')
    await user.keyboard('{Escape}')

    await waitFor(() => {
      expect(useCommandPaletteStore.getState().open).toBe(false)
    })
  })

  /* 5 ── ⌘K keydown toggles */
  it('⌘K keydown toggles the palette open/closed', async () => {
    render(
      <>
        <CommandPalette />
        <LocationDisplay />
      </>,
      { wrapper: createWrapper() },
    )

    // Initially closed.
    expect(useCommandPaletteStore.getState().open).toBe(false)

    // Press Meta+K to open.
    document.dispatchEvent(
      new KeyboardEvent('keydown', { key: 'k', metaKey: true }),
    )
    expect(useCommandPaletteStore.getState().open).toBe(true)

    // Press Meta+K again to close.
    document.dispatchEvent(
      new KeyboardEvent('keydown', { key: 'k', metaKey: true }),
    )
    expect(useCommandPaletteStore.getState().open).toBe(false)
  })

  /* 6 ── Admin gating: non-admin → no Audit Logs; admin → present */
  it('hides admin-only pages (Audit Logs) for non-admin users', async () => {
    useCommandPaletteStore.setState({ open: true })

    // Set non-admin role.
    useAuthStore.setState({
      user: {
        id: 2,
        username: 'viewer',
        email: 'viewer@test',
        role: 'user',
      },
    })

    render(
      <>
        <CommandPalette />
        <LocationDisplay />
      </>,
      { wrapper: createWrapper() },
    )

    await screen.findByPlaceholderText('Search pages, instances, actions…')

    // Audit Logs and LLM Providers should be hidden.
    expect(screen.queryByText('Audit Logs')).not.toBeInTheDocument()
    expect(screen.queryByText('LLM Providers')).not.toBeInTheDocument()

    // But normal pages should be visible.
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('VPN')).toBeInTheDocument()
  })

  it('shows admin-only pages (Audit Logs) for admin users', async () => {
    useCommandPaletteStore.setState({ open: true })

    // Admin user is already set in beforeEach (superadmin).
    render(
      <>
        <CommandPalette />
        <LocationDisplay />
      </>,
      { wrapper: createWrapper() },
    )

    await screen.findByPlaceholderText('Search pages, instances, actions…')

    // Audit Logs and LLM Providers should be visible.
    expect(screen.getByText('Audit Logs')).toBeInTheDocument()
    expect(screen.getByText('LLM Providers')).toBeInTheDocument()
  })

  /* 7 ── Instances group lists seeded instances + selection writes store */
  it('lists instances from API and selecting one writes instance store + navigates', async () => {
    const user = userEvent.setup()
    useCommandPaletteStore.setState({ open: true })
    render(
      <>
        <CommandPalette />
        <LocationDisplay />
      </>,
      { wrapper: createWrapper() },
    )

    await screen.findByPlaceholderText('Search pages, instances, actions…')

    // Wait for instances to load (MSW fixture: edge-berlin-01, edge-oslo-02, edge-vie-03).
    await waitFor(() => {
      expect(screen.getByText('edge-berlin-01')).toBeInTheDocument()
    })
    expect(screen.getByText('edge-oslo-02')).toBeInTheDocument()
    expect(screen.getByText('edge-vie-03')).toBeInTheDocument()

    // Click edge-oslo-02.
    await user.click(screen.getByText('edge-oslo-02'))

    // Instance store should be updated.
    await waitFor(() => {
      expect(useInstanceStore.getState().selectedInstanceId).toBe(2)
    })

    // Navigation to /instances/2.
    await waitFor(() => {
      expect(screen.getByTestId('location')).toHaveTextContent('/instances/2')
    })

    // Palette closed.
    expect(useCommandPaletteStore.getState().open).toBe(false)
  })
})
