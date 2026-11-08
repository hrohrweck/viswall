import { beforeAll, afterAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { http, HttpResponse } from 'msw'

import { MailDomainDetail } from '../pages/Mail/MailDomainDetail'
import { useInstanceStore } from '../stores/instance'
import { server } from './msw/node'

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
/*  Fixtures — dns-records GET + dns-check POST                        */
/* ------------------------------------------------------------------ */

const dnsRecords = {
  domain: 'example.test',
  records: [
    { key: 'mx', type: 'MX', name: 'example.test', value: '10 mail.example.test.', note: null },
    { key: 'spf', type: 'TXT', name: 'example.test', value: 'v=spf1 mx -all', note: null },
    { key: 'dmarc', type: 'TXT', name: '_dmarc.example.test', value: 'v=DMARC1; p=quarantine', note: null },
    { key: 'dkim', type: 'TXT', name: 'mail._domainkey.example.test', value: null, note: 'not_generated' },
  ],
}

const dnsCheck = {
  checked_at: '2026-11-08T12:00:00Z',
  results: [
    { key: 'mx', type: 'MX', name: 'example.test', expected_value: '10 mail.example.test.', found_values: ['10 mail.example.test.'], status: 'correct', detail: null },
    { key: 'spf', type: 'TXT', name: 'example.test', expected_value: 'v=spf1 mx -all', found_values: ['v=spf1 mx -all ip4:203.0.113.7'], status: 'incorrect', detail: null },
    { key: 'dmarc', type: 'TXT', name: '_dmarc.example.test', expected_value: 'v=DMARC1; p=quarantine', found_values: [], status: 'missing', detail: null },
    { key: 'dkim', type: 'TXT', name: 'mail._domainkey.example.test', expected_value: null, found_values: [], status: 'error', detail: 'DNS lookup timed out' },
  ],
}

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
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

function setInstance(id: number | null) {
  useInstanceStore.setState({ selectedInstanceId: id })
}

function renderDetail(initialEntry = '/mail/domains/1') {
  return render(<MailDomainDetail />, {
    wrapper: (p) => <DetailWrapper initialEntry={initialEntry}>{p.children}</DetailWrapper>,
  })
}

async function openDnsTab() {
  server.use(
    http.get('*/mail/domains/:domainId/dns-records', () => HttpResponse.json(dnsRecords)),
    http.post('*/mail/domains/:domainId/dns-check', () => HttpResponse.json(dnsCheck)),
  )
  renderDetail()
  await waitFor(() => {
    expect(screen.getByText('example.test')).toBeInTheDocument()
  })
  await userEvent.click(screen.getByRole('tab', { name: /dns settings/i }))
}

/* ------------------------------------------------------------------ */
/*  setup                                                              */
/* ------------------------------------------------------------------ */

beforeEach(() => {
  setInstance(1)
})

/* ================================================================== */
/*  1 — Records render with names, values and copy affordance          */
/* ================================================================== */

describe('DNS Settings tab records', () => {
  it('renders one row per record with type badge, name, expected value and copy button', async () => {
    await openDnsTab()

    await waitFor(() => {
      expect(screen.getByText('10 mail.example.test.')).toBeInTheDocument()
    })
    expect(screen.getByText('_dmarc.example.test')).toBeInTheDocument()
    expect(screen.getByText('v=spf1 mx -all')).toBeInTheDocument()
    expect(screen.getByText('mail._domainkey.example.test')).toBeInTheDocument()

    // Copy affordance for the three records with a value; none for not_generated dkim
    expect(screen.getAllByTitle('Copy value')).toHaveLength(3)

    // Neutral state before any check has run
    expect(screen.getAllByText('Not checked')).toHaveLength(4)
    expect(screen.queryByText('Last checked:')).not.toBeInTheDocument()
  })

  it('shows the not_generated CTA and opens the DKIM regenerate confirm', async () => {
    await openDnsTab()

    const generateBtn = screen.getByRole('button', { name: /generate dkim key/i })
    expect(generateBtn).toBeInTheDocument()
    await userEvent.click(generateBtn)

    const dialog = await screen.findByRole('dialog')
    expect(within(dialog).getByText(/Generates a new DKIM key for example\.test/)).toBeInTheDocument()
    expect(within(dialog).getByText(/DNS record must be updated/)).toBeInTheDocument()
  })
})

/* ================================================================== */
/*  2 — Live check renders per-record statuses                         */
/* ================================================================== */

describe('DNS Settings live check', () => {
  it('renders mixed statuses, found values and error detail after Check DNS', async () => {
    await openDnsTab()

    await userEvent.click(screen.getByRole('button', { name: /check dns/i }))

    await waitFor(() => {
      expect(screen.getByText('Correct')).toBeInTheDocument()
    })
    expect(screen.getByText('Incorrect')).toBeInTheDocument()
    expect(screen.getByText('Missing')).toBeInTheDocument()
    expect(screen.getByText('Error')).toBeInTheDocument()

    // Incorrect row exposes what DNS actually returns
    expect(screen.getByText('DNS currently returns:')).toBeInTheDocument()
    expect(screen.getByText('v=spf1 mx -all ip4:203.0.113.7')).toBeInTheDocument()

    // Error row exposes the failure detail
    expect(screen.getByText('DNS lookup timed out')).toBeInTheDocument()

    // checked_at surfaced in the header
    await waitFor(() => {
      expect(screen.getByText(/Last checked:/)).toBeInTheDocument()
    })
  })

  it('stays neutral and fires no POST when the tab is only viewed', async () => {
    const checkSpy = vi.fn()
    await openDnsTab()
    server.use(
      http.post('*/mail/domains/:domainId/dns-check', async () => {
        checkSpy()
        return HttpResponse.json(dnsCheck)
      }),
    )

    await waitFor(() => {
      expect(screen.getByText('mail._domainkey.example.test')).toBeInTheDocument()
    })
    expect(screen.getAllByText('Not checked')).toHaveLength(4)
    expect(checkSpy).not.toHaveBeenCalled()
  })
})
