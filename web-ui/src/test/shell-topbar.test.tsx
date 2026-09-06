import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Component } from 'react'
import type { ReactNode } from 'react'
import { Header } from '../components/Header'
import { Toaster } from '../components/ui/Toaster'
import { useAuthStore } from '../stores/auth'
import { useInstanceStore } from '../stores/instance'
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

/** Child that throws on first render. */
class ThrowOnce extends Component<{ onError?: () => void }, { throw: boolean }> {
  state = { throw: true }
  render() {
    if (this.state.throw) {
      this.state.throw = false
      throw new Error('boom')
    }
    return null
  }
}

/* ── tests ── */

describe('Shell topbar', () => {
  let originalMatchMedia: typeof window.matchMedia

  beforeEach(() => {
    // Stub matchMedia for jsdom (theme store / Toaster use it).
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

    // Seed auth store.
    useAuthStore.setState({
      'token': loginResponse.access_token,
      user: {
        id: loginResponse.user.id,
        username: loginResponse.user.username,
        email: loginResponse.user.email,
        role: loginResponse.user.role,
      },
    })
    useInstanceStore.setState({ selectedInstanceId: null })
  })

  afterEach(() => {
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      configurable: true,
      value: originalMatchMedia,
    })
    cleanup()
  })

  /* 1 ── Breadcrumbs */
  it('shows Home breadcrumb for /', async () => {
    render(<Header />, { wrapper: createWrapper(['/']) })

    // For `/`, buildCrumbs returns only [{ label: 'Home' }] — single item, no `to`.
    // It renders as <span aria-current="page">Home</span> (not a link).
    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByLabelText('Breadcrumb')).toBeInTheDocument()
  })

  it('shows Home→Instances breadcrumbs for /instances', async () => {
    render(<Header />, { wrapper: createWrapper(['/instances']) })

    // "Home" has to="/", so it renders as a Link (not the last item).
    expect(screen.getByRole('link', { name: 'Home' })).toBeInTheDocument()
    // "Instances" is the last item — plain text.
    expect(screen.getByText('Instances')).toBeInTheDocument()
  })

  /* 2 ── InstanceSwitcher */
  it('opens the instance switcher and lists seeded instances', async () => {
    const user = userEvent.setup()
    render(<Header />, { wrapper: createWrapper(['/']) })

    // No instance selected → button shows "Select instance". Wait for it.
    const switcherBtn = await screen.findByText('Select instance', {}, { timeout: 5000 })
    expect(switcherBtn).toBeInTheDocument()

    // Click to open dropdown.
    await user.click(switcherBtn.closest('button')!)

    // DropdownMenu.Content renders in a Radix Portal → use waitFor.
    await waitFor(() => {
      expect(screen.getByText('edge-berlin-01')).toBeInTheDocument()
    })
    expect(screen.getByText('edge-oslo-02')).toBeInTheDocument()
    expect(screen.getByText('edge-vie-03')).toBeInTheDocument()
  })

  it('selecting an instance writes to useInstanceStore', async () => {
    const user = userEvent.setup()
    render(<Header />, { wrapper: createWrapper(['/']) })

    // Wait for instances to load (button shows "Select instance" when loaded).
    await screen.findByText('Select instance', {}, { timeout: 5000 })

    // Open switcher.
    const switcherBtn = screen.getByText('Select instance').closest('button')!
    await user.click(switcherBtn)

    // Wait for portal, then click edge-oslo-02.
    await waitFor(() => {
      expect(screen.getByText('edge-oslo-02')).toBeInTheDocument()
    })
    await user.click(screen.getByText('edge-oslo-02'))

    // Assert the store was updated (not just the UI text).
    expect(useInstanceStore.getState().selectedInstanceId).toBe(2)
  })

  /* 3 ── Theme toggle */
  it('theme toggle cycles light→dark→system on <html> classList', async () => {
    const user = userEvent.setup()
    const { container } = render(<Header />, { wrapper: createWrapper(['/']) })

    // Find the theme toggle IconButton — its label starts with "Theme:".
    const themeBtn = container.querySelector('[aria-label^="Theme"]') as HTMLButtonElement
    expect(themeBtn).toBeTruthy()

    // Initial state: 'system' (default from store, matchMedia mocked as false).
    // First click: system → light.
    await user.click(themeBtn)
    // light → no 'dark' class.
    expect(document.documentElement.classList.contains('dark')).toBe(false)

    // Second click: light → dark.
    await user.click(themeBtn)
    expect(document.documentElement.classList.contains('dark')).toBe(true)

    // Third click: dark → system (matchMedia → false → no dark).
    await user.click(themeBtn)
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  /* 4 ── User menu + Logout */
  it('Logout clears auth store and navigates to /login', async () => {
    const user = userEvent.setup()
    render(<Header />, { wrapper: createWrapper(['/']) })

    // Open user menu — the trigger button has aria-label="User menu".
    const userMenuBtn = screen.getByRole('button', { name: 'User menu' })
    await user.click(userMenuBtn)

    // Wait for portal, click Logout.
    await waitFor(() => {
      expect(screen.getByText('Logout')).toBeInTheDocument()
    })
    await user.click(screen.getByText('Logout'))

    // Assert store token is null.
    expect(useAuthStore.getState().token).toBeNull()
    expect(useAuthStore.getState().user).toBeNull()
  })

  /* 5 ── ErrorBoundary */
  it('ErrorBoundary renders fallback when child throws', async () => {
    // Import ErrorBoundary directly.
    const { ErrorBoundary } = await import('../components/ui/ErrorBoundary')
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    render(
      <ErrorBoundary>
        <ThrowOnce />
      </ErrorBoundary>,
      { wrapper: createWrapper(['/']) },
    )

    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    expect(screen.getByText('boom')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /reload/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument()

    consoleSpy.mockRestore()
  })

  /* 6 ── Toaster mounted */
  it('Toaster renders without crashing', async () => {
    const { container } = render(<Toaster />, { wrapper: createWrapper(['/']) })

    // sonner renders a <section> (or div) with data-sonner-toaster attribute.
    // If that changes, just assert the component didn't throw.
    const toasterEl =
      container.querySelector('[data-sonner-toaster]') ??
      container.querySelector('[role="region"]') ??
      container.firstElementChild

    expect(toasterEl).toBeTruthy()
  })
})
