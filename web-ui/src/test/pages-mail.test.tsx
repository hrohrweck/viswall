import { beforeAll, afterAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { http, HttpResponse } from 'msw'

import { MailDomains } from '../pages/Mail/MailDomains'
import { MailDomainDetail } from '../pages/Mail/MailDomainDetail'
import { MailDomainCreate } from '../pages/Mail/MailDomainCreate'
import { MailClassificationView } from '../pages/Mail/MailClassificationView'
import { useInstanceStore } from '../stores/instance'
import { server } from './msw/node'
import { mailDomains } from './msw/fixtures'

/* ------------------------------------------------------------------ */
/*  ResizeObserver polyfill — Radix useSize                            */
/* ------------------------------------------------------------------ */

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
/*  Helpers                                                            */
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
          <Route path="/mail/domains/:id" element={children} />
          <Route path="/mail" element={<div>Mail list</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

function CreateWrapper({ children }: { children: React.ReactNode }) {
  const qc = makeQueryClient()
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        {children}
      </MemoryRouter>
    </QueryClientProvider>
  )
}

function setInstance(id: number | null) {
  useInstanceStore.setState({ selectedInstanceId: id })
}

/* ------------------------------------------------------------------ */
/*  setup                                                              */
/* ------------------------------------------------------------------ */

beforeEach(() => {
  setInstance(1)
})

/* ================================================================== */
/*  1 — Instance-notice when no instance selected                      */
/* ================================================================== */

describe('MailDomains instance-notice', () => {
  it('shows instance-notice Card when no instance selected', () => {
    setInstance(null)
    render(<MailDomains />, { wrapper: Wrapper })
    expect(screen.getByText('Mail Domains')).toBeInTheDocument()
    expect(
      screen.getByText('Select an instance from the top bar to manage its mail domains.'),
    ).toBeInTheDocument()
  })

  it('does not render raw InstanceSelector when no instance selected', () => {
    setInstance(null)
    render(<MailDomains />, { wrapper: Wrapper })
    expect(screen.queryByRole('combobox')).not.toBeInTheDocument()
  })
})

/* ================================================================== */
/*  2 — DKIM regenerate confirm shows impact                           */
/* ================================================================== */

describe('DKIM regenerate confirm', () => {
  it('shows impact text in DKIM confirm dialog', async () => {
    render(<MailDomainDetail />, { wrapper: (p) => <DetailWrapper initialEntry="/mail/domains/1">{p.children}</DetailWrapper> })

    await waitFor(() => {
      expect(screen.getByText('example.test')).toBeInTheDocument()
    })

    // Open the kebab menu
    const kebab = screen.getByLabelText('Domain actions')
    await userEvent.click(kebab)

    // Click Regenerate DKIM
    const dkimItem = await screen.findByText('Regenerate DKIM')
    await userEvent.click(dkimItem)

    // ConfirmDialog should appear with impact
    const dialog = await screen.findByRole('dialog')
    expect(dialog).toBeInTheDocument()
    expect(within(dialog).getByText(/Generates a new DKIM key for example\.test/)).toBeInTheDocument()
    expect(within(dialog).getByText(/DNS record must be updated/)).toBeInTheDocument()
  })
})

/* ================================================================== */
/*  3 — Delete domain confirm shows impact                             */
/* ================================================================== */

describe('Delete domain confirm', () => {
  it('shows impact text in delete domain dialog', async () => {
    render(<MailDomainDetail />, { wrapper: (p) => <DetailWrapper initialEntry="/mail/domains/1">{p.children}</DetailWrapper> })

    await waitFor(() => {
      expect(screen.getByText('example.test')).toBeInTheDocument()
    })

    // Open kebab → Delete Domain
    await userEvent.click(screen.getByLabelText('Domain actions'))
    const deleteItem = await screen.findByText('Delete Domain')
    await userEvent.click(deleteItem)

    const dialog = await screen.findByRole('dialog')
    expect(within(dialog).getByText(/Removes example\.test including mailboxes and DNS records/)).toBeInTheDocument()
  })
})

/* ================================================================== */
/*  3b — Delete domain mutation                                        */
/* ================================================================== */

describe('Delete domain mutation', () => {
  it('fires DELETE, shows success toast and navigates to /mail', async () => {
    const { toast } = await import('sonner')
    const deleteSpy = vi.fn()
    server.use(
      http.delete('*/mail/domains/:domainId', async () => {
        deleteSpy()
        return HttpResponse.json({ status: 'ok' })
      }),
    )

    render(<MailDomainDetail />, { wrapper: (p) => <DetailWrapper initialEntry="/mail/domains/1">{p.children}</DetailWrapper> })

    await waitFor(() => {
      expect(screen.getByText('example.test')).toBeInTheDocument()
    })

    // Open kebab → Delete Domain
    await userEvent.click(screen.getByLabelText('Domain actions'))
    const deleteItem = await screen.findByText('Delete Domain')
    await userEvent.click(deleteItem)

    const dialog = await screen.findByRole('dialog')
    const confirmBtn = within(dialog).getByRole('button', { name: /delete/i })
    await userEvent.click(confirmBtn)

    await waitFor(() => expect(deleteSpy).toHaveBeenCalledTimes(1))
    await waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith(expect.stringContaining('deleted'))
    })
    await waitFor(() => {
      expect(screen.getByText('Mail list')).toBeInTheDocument()
    })
  })

  it('shows error toast and keeps dialog open when DELETE fails', async () => {
    const { toast } = await import('sonner')
    server.use(
      http.delete('*/mail/domains/:domainId', () => HttpResponse.json({ detail: 'boom' }, { status: 500 })),
    )

    render(<MailDomainDetail />, { wrapper: (p) => <DetailWrapper initialEntry="/mail/domains/1">{p.children}</DetailWrapper> })

    await waitFor(() => {
      expect(screen.getByText('example.test')).toBeInTheDocument()
    })

    // Open kebab → Delete Domain
    await userEvent.click(screen.getByLabelText('Domain actions'))
    const deleteItem = await screen.findByText('Delete Domain')
    await userEvent.click(deleteItem)

    const dialog = await screen.findByRole('dialog')
    await userEvent.click(within(dialog).getByRole('button', { name: /delete/i }))

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(expect.stringContaining('boom'))
    })

    // Dialog stays open — confirm button is still visible
    await waitFor(() => {
      const openDialog = screen.getByRole('dialog')
      expect(openDialog).toBeInTheDocument()
      expect(within(openDialog).getByRole('button', { name: /delete/i })).toBeInTheDocument()
    })
    expect(screen.queryByText('Mail list')).not.toBeInTheDocument()
  })
})

/* ================================================================== */
/*  4 — Groupware toggle confirm                                       */
/* ================================================================== */

describe('Groupware toggle confirm', () => {
  it('shows confirm dialog when toggling groupware', async () => {
    render(<MailDomainDetail />, { wrapper: (p) => <DetailWrapper initialEntry="/mail/domains/1">{p.children}</DetailWrapper> })

    await waitFor(() => {
      expect(screen.getByText('example.test')).toBeInTheDocument()
    })

    // Switch to Groupware tab
    const groupwareTab = screen.getByRole('tab', { name: /groupware/i })
    await userEvent.click(groupwareTab)

    // Click the groupware toggle switch
    const toggle = screen.getByLabelText('Toggle groupware')
    await userEvent.click(toggle)

    const dialog = await screen.findByRole('dialog')
    expect(dialog).toBeInTheDocument()
    expect(within(dialog).getByText(/Disable SOGo groupware/)).toBeInTheDocument()
  })
})

/* ================================================================== */
/*  5 — Classification: Deliver + Reclassify confirm before fire       */
/* ================================================================== */

describe('Classification confirm-before-fire', () => {
  it('Deliver opens ConfirmDialog before firing mutation', async () => {
    const mutateSpy = vi.fn()
    server.use(
      http.post('*/mail/messages/:id/action', async () => {
        mutateSpy()
        return HttpResponse.json({ id: 1, status: 'ok' })
      }),
    )

    render(<MailClassificationView domainId={1} />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByText('Weekly Tech Newsletter #42')).toBeInTheDocument()
    })

    // Find the Deliver button (CheckCircle icon) — in the row actions
    const deliverBtns = screen.getAllByTitle('Deliver')
    await userEvent.click(deliverBtns[0])

    const dialog = await screen.findByRole('dialog')
    expect(dialog).toBeInTheDocument()
    expect(mutateSpy).not.toHaveBeenCalled()

    // Confirm
    const confirmBtn = within(dialog).getByRole('button', { name: /deliver/i })
    await userEvent.click(confirmBtn)

    await waitFor(() => expect(mutateSpy).toHaveBeenCalledTimes(1))
  })

  it('Reclassify opens ConfirmDialog before firing mutation', async () => {
    const mutateSpy = vi.fn()
    server.use(
      http.post('*/mail/messages/:id/reclassify', async () => {
        mutateSpy()
        return HttpResponse.json({ id: 1, status: 'reclassified' })
      }),
    )

    render(<MailClassificationView domainId={1} />, { wrapper: Wrapper })

    await waitFor(() => {
      expect(screen.getByText('Weekly Tech Newsletter #42')).toBeInTheDocument()
    })

    const reclassifyBtns = screen.getAllByTitle('Reclassify')
    await userEvent.click(reclassifyBtns[0])

    const dialog = await screen.findByRole('dialog')
    expect(dialog).toBeInTheDocument()
    expect(mutateSpy).not.toHaveBeenCalled()

    const confirmBtn = within(dialog).getByRole('button', { name: /reclassify/i })
    await userEvent.click(confirmBtn)

    await waitFor(() => expect(mutateSpy).toHaveBeenCalledTimes(1))
  })
})

/* ================================================================== */
/*  6 — Add mailbox via extracted form + toast                         */
/* ================================================================== */

describe('Add mailbox via extracted form', () => {
  it('submits new mailbox and shows success toast', async () => {
    const { toast } = await import('sonner')
    render(<MailDomainDetail />, { wrapper: (p) => <DetailWrapper initialEntry="/mail/domains/1">{p.children}</DetailWrapper> })

    await waitFor(() => {
      expect(screen.getByText('example.test')).toBeInTheDocument()
    })

    // Click Add Mailbox
    const addBtn = screen.getByRole('button', { name: /add mailbox/i })
    await userEvent.click(addBtn)

    const modal = await screen.findByRole('dialog')
    expect(modal).toBeInTheDocument()

    // Fill the form
    const usernameInput = within(modal).getByLabelText('Username')
    await userEvent.type(usernameInput, 'newuser')

    const createBtn = within(modal).getByRole('button', { name: /create/i })
    await userEvent.click(createBtn)

    await waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith(expect.stringContaining('newuser@example.test'))
    })
  })
})

/* ================================================================== */
/*  7 — Not-found shows EmptyState (not bare <p>)                      */
/* ================================================================== */

describe('MailDomainDetail not-found', () => {
  it('shows EmptyState when domain is not found (404)', async () => {
    render(<MailDomainDetail />, { wrapper: (p) => <DetailWrapper initialEntry="/mail/domains/999">{p.children}</DetailWrapper> })

    await waitFor(() => {
      expect(screen.getByText('Domain not found')).toBeInTheDocument()
    })
    expect(screen.getByText('Back to Mail Domains')).toBeInTheDocument()
    // Should NOT show bare <p>Domain not found.</p>
    expect(screen.queryByText('Domain not found.')).not.toBeInTheDocument()
  })
})

/* ================================================================== */
/*  8 — Wizard reaches Review step and shows values                    */
/* ================================================================== */

describe('MailDomainCreate wizard Review step', () => {
  it('reaches Review step and displays chosen values', async () => {
    render(<MailDomainCreate />, { wrapper: CreateWrapper })

    // Step 1: Enter domain
    const domainInput = screen.getByPlaceholderText('example.com')
    await userEvent.type(domainInput, 'test.example')

    // Continue to step 2
    const continueBtn = screen.getByRole('button', { name: /continue/i })
    await userEvent.click(continueBtn)

    // Step 2: Security toggles — should be visible
    await waitFor(() => {
      expect(screen.getByText('SpamAssassin Filter')).toBeInTheDocument()
    })

    // Continue to step 3 (Review)
    await userEvent.click(continueBtn)

    // Step 3: Review should show values
    await waitFor(() => {
      expect(screen.getByText('Review configuration')).toBeInTheDocument()
    })

    // Should display domain name in the review table
    expect(screen.getByText('test.example')).toBeInTheDocument()
    expect(screen.getAllByText('Enabled').length).toBeGreaterThan(3)
    // Create Domain button should be present
    expect(screen.getByRole('button', { name: /create domain/i })).toBeInTheDocument()
  })
})

/* ================================================================== */
/*  9 — Forwarding tab renders grouped aliases                         */
/* ================================================================== */

describe('MailDomainDetail forwarding tab', () => {
  it('renders grouped alias rows with destinations and Catch-all badge', async () => {
    render(<MailDomainDetail />, { wrapper: (p) => <DetailWrapper initialEntry="/mail/domains/1">{p.children}</DetailWrapper> })

    await waitFor(() => {
      expect(screen.getByText('example.test')).toBeInTheDocument()
    })

    await userEvent.click(screen.getByRole('tab', { name: /forwarding/i }))

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Forwarding' })).toBeInTheDocument()
    })

    // Grouped by source: one row per source with joined destinations
    expect(screen.getByText('sales@example.test')).toBeInTheDocument()
    expect(screen.getByText('alice@example.test, bob@example.test')).toBeInTheDocument()
    expect(screen.getByText('support@example.test')).toBeInTheDocument()
    expect(screen.getByText('carol@external.test')).toBeInTheDocument()
    // Catch-all source renders with a badge
    expect(screen.getByText('*@example.test')).toBeInTheDocument()
    expect(screen.getByText('Catch-all')).toBeInTheDocument()
    // No per-destination duplicate rows for multi-destination sources
    expect(screen.getAllByText(/sales@example\.test/).length).toBe(1)
  })
})

/* ================================================================== */
/*  10 — Forwarding: create alias fires one POST per destination       */
/* ================================================================== */

describe('Forwarding create alias', () => {
  it('submits two destinations as two POSTs and shows success toast', async () => {
    const { toast } = await import('sonner')
    const posts: Array<Record<string, unknown>> = []
    server.use(
      http.post('*/mail/aliases/:domainId', async ({ request }) => {
        const body = (await request.json()) as Record<string, unknown>
        posts.push(body)
        return HttpResponse.json({ id: 99, domain_id: 1, ...body })
      }),
    )

    render(<MailDomainDetail />, { wrapper: (p) => <DetailWrapper initialEntry="/mail/domains/1">{p.children}</DetailWrapper> })

    await waitFor(() => {
      expect(screen.getByText('example.test')).toBeInTheDocument()
    })
    await userEvent.click(screen.getByRole('tab', { name: /forwarding/i }))

    await userEvent.click(screen.getByRole('button', { name: /add alias/i }))
    const modal = await screen.findByRole('dialog')
    expect(within(modal).getByText('Add Alias')).toBeInTheDocument()

    await userEvent.type(within(modal).getByLabelText('Source'), 'team')
    await userEvent.type(within(modal).getByLabelText('Destination 1'), 'd1@example.test')
    await userEvent.click(within(modal).getByRole('button', { name: /add destination/i }))
    await userEvent.type(within(modal).getByLabelText('Destination 2'), 'd2@example.test')

    await userEvent.click(within(modal).getByRole('button', { name: /create alias/i }))

    await waitFor(() => expect(posts).toHaveLength(2))
    expect(posts.map((p) => p.source)).toEqual(['team', 'team'])
    expect(posts.map((p) => p.destination)).toEqual(['d1@example.test', 'd2@example.test'])
    expect(posts.map((p) => p.enabled)).toEqual([true, true])

    await waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith(expect.stringContaining('Alias "team" created'))
    })
  })
})

/* ================================================================== */
/*  11 — Forwarding: toggle fires one PATCH per row of the group       */
/* ================================================================== */

describe('Forwarding toggle alias', () => {
  it('fires a PATCH per alias row when the group switch is clicked', async () => {
    const patches: Array<{ id: number; body: Record<string, unknown> }> = []
    server.use(
      http.patch('*/mail/aliases/:aliasId', async ({ request, params }) => {
        const body = (await request.json()) as Record<string, unknown>
        patches.push({ id: Number(params.aliasId), body })
        return HttpResponse.json({ id: Number(params.aliasId), ...body })
      }),
    )

    render(<MailDomainDetail />, { wrapper: (p) => <DetailWrapper initialEntry="/mail/domains/1">{p.children}</DetailWrapper> })

    await waitFor(() => {
      expect(screen.getByText('example.test')).toBeInTheDocument()
    })
    await userEvent.click(screen.getByRole('tab', { name: /forwarding/i }))

    // sales group has two rows (ids 1 and 2) and is currently enabled
    await userEvent.click(await screen.findByLabelText('Active: sales'))

    await waitFor(() => expect(patches).toHaveLength(2))
    expect(patches.map((p) => p.id).sort()).toEqual([1, 2])
    expect(patches.map((p) => p.body)).toEqual([{ enabled: false }, { enabled: false }])
  })
})

/* ================================================================== */
/*  12 — Forwarding: delete group fires one DELETE per row + toast     */
/* ================================================================== */

describe('Forwarding delete alias', () => {
  it('confirms then fires a DELETE per alias row and shows success toast', async () => {
    const { toast } = await import('sonner')
    const deletes: number[] = []
    server.use(
      http.delete('*/mail/aliases/:aliasId', ({ params }) => {
        deletes.push(Number(params.aliasId))
        return HttpResponse.json({ status: 'ok' })
      }),
    )

    render(<MailDomainDetail />, { wrapper: (p) => <DetailWrapper initialEntry="/mail/domains/1">{p.children}</DetailWrapper> })

    await waitFor(() => {
      expect(screen.getByText('example.test')).toBeInTheDocument()
    })
    await userEvent.click(screen.getByRole('tab', { name: /forwarding/i }))

    const salesRow = (await screen.findByText('sales@example.test')).closest('tr') as HTMLTableRowElement
    await userEvent.click(within(salesRow).getByLabelText('Actions'))
    await userEvent.click(await screen.findByText('Delete'))

    const dialog = await screen.findByRole('dialog')
    expect(within(dialog).getByText(/Delete "sales@example\.test"/)).toBeInTheDocument()
    expect(within(dialog).getByText(/alice@example\.test, bob@example\.test/)).toBeInTheDocument()

    await userEvent.click(within(dialog).getByRole('button', { name: /delete/i }))

    await waitFor(() => expect(deletes.sort()).toEqual([1, 2]))
    await waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith(expect.stringContaining('deleted'))
    })
  })
})

/* ================================================================== */
/*  13 — Forwarding: edit diffs destinations into POST + DELETE        */
/* ================================================================== */

describe('Forwarding edit alias', () => {
  it('diffs destination changes into one POST and one DELETE', async () => {
    const { toast } = await import('sonner')
    const posts: Array<Record<string, unknown>> = []
    const deletes: number[] = []
    server.use(
      http.post('*/mail/aliases/:domainId', async ({ request }) => {
        const body = (await request.json()) as Record<string, unknown>
        posts.push(body)
        return HttpResponse.json({ id: 99, domain_id: 1, ...body })
      }),
      http.delete('*/mail/aliases/:aliasId', ({ params }) => {
        deletes.push(Number(params.aliasId))
        return HttpResponse.json({ status: 'ok' })
      }),
    )

    render(<MailDomainDetail />, { wrapper: (p) => <DetailWrapper initialEntry="/mail/domains/1">{p.children}</DetailWrapper> })

    await waitFor(() => {
      expect(screen.getByText('example.test')).toBeInTheDocument()
    })
    await userEvent.click(screen.getByRole('tab', { name: /forwarding/i }))

    const salesRow = (await screen.findByText('sales@example.test')).closest('tr') as HTMLTableRowElement
    await userEvent.click(within(salesRow).getByLabelText('Actions'))
    await userEvent.click(await screen.findByText('Edit'))

    const modal = await screen.findByRole('dialog')
    expect(within(modal).getByText('Edit Alias')).toBeInTheDocument()
    // Source is disabled in edit mode
    expect(within(modal).getByLabelText('Source')).toBeDisabled()

    // Remove bob, add carol
    await userEvent.click(within(modal).getByLabelText('Remove destination 2'))
    await userEvent.click(within(modal).getByRole('button', { name: /add destination/i }))
    await userEvent.type(within(modal).getByLabelText('Destination 2'), 'carol@example.test')

    await userEvent.click(within(modal).getByRole('button', { name: /save changes/i }))

    await waitFor(() => expect(deletes).toEqual([2]))
    await waitFor(() => expect(posts).toHaveLength(1))
    expect(posts[0]).toMatchObject({
      source: 'sales',
      destination: 'carol@example.test',
      enabled: true,
    })

    await waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith(expect.stringContaining('updated'))
    })
  })
})
