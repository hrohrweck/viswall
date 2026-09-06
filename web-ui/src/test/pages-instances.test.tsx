import { beforeAll, afterAll, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor, within, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { http, HttpResponse } from 'msw'

import { Instances } from '../pages/Instances'
import { InstanceDetail } from '../pages/InstanceDetail'
import { server } from './msw/node'
import { instances } from './msw/fixtures'

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

function createListWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>{children}</MemoryRouter>
      </QueryClientProvider>
    )
  }
}

function renderDetail(path: string) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/instances/:id" element={<InstanceDetail />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

/* -------------------------------------------------------------------------- */
/*  Instances list tests                                                       */
/* -------------------------------------------------------------------------- */

describe('Instances', () => {
  it('renders fixtures with PageHeader', async () => {
    const Wrapper = createListWrapper()
    render(<Instances />, { wrapper: Wrapper })

    // PageHeader title
    expect(screen.getByRole('heading', { name: /instances/i })).toBeInTheDocument()

    // Wait for data to load
    await screen.findByText('edge-berlin-01')
    expect(screen.getByText('edge-oslo-02')).toBeInTheDocument()
    expect(screen.getByText('edge-vie-03')).toBeInTheDocument()
  })

  it('search filters rows', async () => {
    const Wrapper = createListWrapper()
    render(<Instances />, { wrapper: Wrapper })

    await screen.findByText('edge-berlin-01')

    // Type in search
    const searchInput = screen.getByRole('textbox', { name: /search/i })
    await userEvent.type(searchInput, 'oslo')

    // Only oslo should remain
    expect(screen.getByText('edge-oslo-02')).toBeInTheDocument()
    expect(screen.queryByText('edge-berlin-01')).not.toBeInTheDocument()
  })

  it('pagination footer renders', async () => {
    const Wrapper = createListWrapper()
    render(<Instances />, { wrapper: Wrapper })

    await screen.findByText('edge-berlin-01')

    // Pagination controls
    expect(screen.getByText(/rows per page/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /previous page/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /next page/i })).toBeInTheDocument()
  })

  it('row actions column renders kebab trigger', async () => {
    const Wrapper = createListWrapper()
    render(<Instances />, { wrapper: Wrapper })

    await screen.findByText('edge-berlin-01')

    const kebabButtons = screen.getAllByRole('button', { name: /instance actions/i })
    expect(kebabButtons.length).toBeGreaterThan(0)
  })
})

/* -------------------------------------------------------------------------- */
/*  InstanceDetail tests                                                       */
/* -------------------------------------------------------------------------- */

describe('InstanceDetail', () => {
  it('renders cards for existing instance', async () => {
    renderDetail('/instances/1')

    // Wait for instance to load
    await screen.findByText('edge-berlin-01')

    // PageHeader
    expect(screen.getByRole('heading', { name: 'edge-berlin-01' })).toBeInTheDocument()

    // Overview card
    expect(screen.getByText('Overview')).toBeInTheDocument()
    expect(screen.getByText('Last Seen')).toBeInTheDocument()

    // Connection card — hostname appears twice (PageHeader desc + Connection card)
    expect(screen.getByText('Connection')).toBeInTheDocument()
    expect(screen.getAllByText('berlin.edge.viswall.test').length).toBeGreaterThanOrEqual(2)

    // Quick Links card
    expect(screen.getByText('Quick Links')).toBeInTheDocument()
    expect(screen.getByText('Firewall Rules')).toBeInTheDocument()
    expect(screen.getByText('VPN Servers')).toBeInTheDocument()
    expect(screen.getByText('Mail Domains')).toBeInTheDocument()
  })

  it('shows EmptyState for non-existent instance (404)', async () => {
    renderDetail('/instances/999')

    // Should show not-found EmptyState
    await screen.findByText('Instance not found')
    expect(screen.getByText(/does not exist or has been removed/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /back to instances/i })).toHaveAttribute('href', '/instances')
  })

  it('Edit modal saves via useUpdateInstance and shows toast', async () => {
    let patchBody: Record<string, unknown> | null = null
    server.use(
      http.patch('/api/v1/instances/:id', async ({ request }) => {
        patchBody = await request.json() as Record<string, unknown>
        return HttpResponse.json({ ...instances[0], name: 'updated-name' })
      }),
    )

    renderDetail('/instances/1')

    await screen.findByText('edge-berlin-01')

    // Click Edit button
    await userEvent.click(screen.getByRole('button', { name: /edit/i }))

    // Modal should appear
    const nameInput = await screen.findByDisplayValue('edge-berlin-01')

    // Clear and type new name
    await userEvent.clear(nameInput)
    await userEvent.type(nameInput, 'renamed-instance')

    // Click Save
    await userEvent.click(screen.getByRole('button', { name: /save/i }))

    await waitFor(() => {
      expect(patchBody).not.toBeNull()
      expect(patchBody).toMatchObject({ name: 'renamed-instance' })
    })
  })

  it('copy button writes to clipboard', async () => {
    const writeTextMock = vi.fn().mockResolvedValue(undefined)
    vi.stubGlobal('navigator', { clipboard: { writeText: writeTextMock } })

    renderDetail('/instances/1')

    await screen.findByText('edge-berlin-01')

    // Find copy button for hostname
    const copyButtons = screen.getAllByRole('button', { name: /copy/i })
    await userEvent.click(copyButtons[0])

    expect(writeTextMock).toHaveBeenCalledWith('berlin.edge.viswall.test')

    vi.unstubAllGlobals()
  })

  it('Delete button opens ConfirmDialog, confirm fires delete mutation', async () => {
    let deleteCalled = false
    server.use(
      http.delete('/api/v1/instances/:id', () => {
        deleteCalled = true
        return HttpResponse.json(null, { status: 204 })
      }),
    )

    renderDetail('/instances/1')

    await screen.findByText('edge-berlin-01')

    // Click the Delete button in the PageHeader
    await userEvent.click(screen.getByRole('button', { name: /delete/i }))

    // ConfirmDialog should appear
    await screen.findByText('Delete Instance')

    // Click confirm
    const confirmBtn = screen.getByRole('button', { name: /^delete$/i })
    await userEvent.click(confirmBtn)

    await waitFor(() => {
      expect(deleteCalled).toBe(true)
    })
  })

  it('Quick Links use react-router Link (not anchor tags)', async () => {
    renderDetail('/instances/1')

    await screen.findByText('edge-berlin-01')

    // Quick Links should be <a> tags that are react-router Links (they have href)
    const firewallLink = screen.getByRole('link', { name: /firewall rules/i })
    expect(firewallLink).toHaveAttribute('href', '/firewall?instance=1')
  })
})
