import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { act, cleanup, render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Header } from '../components/Header'
import { Layout } from '../components/Layout'
import { useAuthStore } from '../stores/auth'
import { useSidebarStore } from '../stores/sidebar'
import { useInstanceStore } from '../stores/instance'
import { loginResponse } from './msw/fixtures'

const DESKTOP_QUERY = '(min-width: 1024px)'

function stubMatchMedia(desktop = false) {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    configurable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: query === DESKTOP_QUERY ? desktop : false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  })
}

function seedStores() {
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
  useSidebarStore.setState({ collapsed: false, mobileOpen: false })
}

function renderLayout(entries: string[] = ['/']) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  const router = createMemoryRouter(
    [
      {
        path: '*',
        element: <Layout />,
        children: [
          { index: true, element: <div>Dashboard page</div> },
          { path: 'instances', element: <div>Instances page</div> },
        ],
      },
    ],
    { initialEntries: entries },
  )
  return render(
    <QueryClientProvider client={qc}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )
}

describe('Shell responsive', () => {
  let originalMatchMedia: typeof window.matchMedia

  beforeEach(() => {
    originalMatchMedia = window.matchMedia
    stubMatchMedia(false)
    seedStores()
  })

  afterEach(() => {
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      configurable: true,
      value: originalMatchMedia,
    })
    useSidebarStore.setState({ mobileOpen: false })
    document.body.style.overflow = ''
    cleanup()
  })

  it('drawer wrapper has translate-x-[-100%] when closed and translate-x-0 when open', () => {
    useSidebarStore.setState({ mobileOpen: false })
    const { container } = renderLayout()

    const drawerWrapper = container.querySelector('.fixed.inset-y-0')
    expect(drawerWrapper).toBeTruthy()
    expect(drawerWrapper!.className).toContain('translate-x-[-100%]')
    expect(screen.queryByTestId('sidebar-scrim')).not.toBeInTheDocument()

    act(() => {
      useSidebarStore.setState({ mobileOpen: true })
    })

    expect(drawerWrapper!.className).toContain('translate-x-0')
    expect(screen.getByTestId('sidebar-scrim')).toBeInTheDocument()
  })

  it('hamburger button has correct aria-label and toggles store', async () => {
    const user = userEvent.setup()
    renderLayout()

    const openBtn = screen.getByRole('button', { name: 'Open navigation' })
    expect(openBtn).toBeInTheDocument()

    await user.click(openBtn)
    expect(useSidebarStore.getState().mobileOpen).toBe(true)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Close navigation' })).toBeInTheDocument()
    })
  })

  it('Escape key closes the drawer', async () => {
    useSidebarStore.setState({ mobileOpen: true })
    renderLayout()

    expect(screen.getByTestId('sidebar-scrim')).toBeInTheDocument()

    fireEvent.keyDown(document, { key: 'Escape' })

    await waitFor(() => {
      expect(useSidebarStore.getState().mobileOpen).toBe(false)
    })
  })

  it('route change closes the drawer', async () => {
    useSidebarStore.setState({ mobileOpen: true })
    renderLayout()

    expect(screen.getByTestId('sidebar-scrim')).toBeInTheDocument()

    const instancesLink = screen.getByRole('link', { name: 'Instances' })
    const user = userEvent.setup()
    await user.click(instancesLink)

    await waitFor(() => {
      expect(useSidebarStore.getState().mobileOpen).toBe(false)
    })
  })

  it('hamburger has lg:hidden class for desktop viewport hiding', () => {
    stubMatchMedia(true)
    renderLayout()

    const hamburger = screen.getByRole('button', { name: 'Open navigation' })
    expect(hamburger.className).toContain('lg:hidden')
  })
})
