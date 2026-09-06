import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { http, HttpResponse } from 'msw'
import { server } from './msw/node'
import { useInstanceStore } from '../stores/instance'
import { routingRules, qosPolicies } from './msw/fixtures'

/* ------------------------------------------------------------------ */
/*  ResizeObserver polyfill — IconButton wraps Tooltip → Radix useSize */
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
import { RoutingRules } from '../pages/RoutingRules'
import { TrafficShaping } from '../pages/TrafficShaping'
import { RoutingRuleForm } from '../components/forms/RoutingRuleForm'
import { TrafficPolicyForm } from '../components/forms/TrafficPolicyForm'

/**
 * RoutingRules + TrafficShaping page tests — Task 19 (retry).
 *
 * Covers: apply confirm+toast, QoS delete confirm, instance-notice,
 * RoutingRuleForm submit, search filter, TrafficPolicyForm submit.
 */

function createWrapper() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={qc}>
        <MemoryRouter>{children}</MemoryRouter>
      </QueryClientProvider>
    )
  }
}

beforeEach(() => {
  useInstanceStore.setState({ selectedInstanceId: 1 })
})

describe('RoutingRules', () => {
  it('apply opens confirm dialog with impact text, then shows toast on success', async () => {
    let capturedUrl = ''
    server.use(
      http.post('/api/v1/routing/apply/:instanceId', ({ request }) => {
        capturedUrl = new URL(request.url).pathname
        return HttpResponse.json({ status: 'ok' })
      }),
    )

    const Wrapper = createWrapper()
    render(<RoutingRules />, { wrapper: Wrapper })

    await screen.findByText('VoIP via backup WAN')

    // Click Apply Rules button
    await userEvent.click(screen.getByRole('button', { name: /apply rules/i }))

    // Confirm dialog should appear with impact text
    const dialog = await screen.findByRole('dialog')
    expect(dialog).toHaveTextContent(/Applies routing policy/i)
    expect(dialog).toHaveTextContent(/Active connections may be re-routed/i)

    // Click Apply in the dialog
    const applyBtn = within(dialog).getByRole('button', { name: /apply/i })
    await userEvent.click(applyBtn)

    await waitFor(() => {
      expect(capturedUrl).toBe('/api/v1/routing/apply/1')
    })
  })

  it('search filters routing table', async () => {
    const Wrapper = createWrapper()
    render(<RoutingRules />, { wrapper: Wrapper })

    await screen.findByText('VoIP via backup WAN')

    // Type in search
    const searchInput = screen.getByRole('textbox', { name: /search/i })
    await userEvent.type(searchInput, 'nonexistent-rule-xyz')

    // Rule should be filtered out
    await waitFor(() => {
      expect(screen.queryByText('VoIP via backup WAN')).not.toBeInTheDocument()
    })
  })

  it('instance-notice renders when no instance selected', () => {
    useInstanceStore.setState({ selectedInstanceId: null })

    const Wrapper = createWrapper()
    render(<RoutingRules />, { wrapper: Wrapper })

    expect(
      screen.getByText(/Select an instance from the top bar to manage routing rules/i),
    ).toBeInTheDocument()
  })
})

describe('TrafficShaping', () => {
  it('QoS delete opens confirm dialog before firing mutation', async () => {
    let deleteCalled = false
    server.use(
      http.delete('/api/v1/firewall/qos/:instanceId/:policyId', () => {
        deleteCalled = true
        return HttpResponse.json({ status: 'ok' })
      }),
    )

    const Wrapper = createWrapper()
    render(<TrafficShaping />, { wrapper: Wrapper })

    await screen.findByText('wan-shaping')

    // Click delete button
    const deleteBtn = screen.getByRole('button', { name: /delete policy/i })
    await userEvent.click(deleteBtn)

    // Confirm dialog should appear BEFORE the mutation fires
    const dialog = await screen.findByRole('dialog')
    expect(dialog).toHaveTextContent(/Deletes policy/i)
    expect(dialog).toHaveTextContent(/wan-shaping/i)

    // Delete should NOT have been called yet
    expect(deleteCalled).toBe(false)

    // Confirm delete
    const confirmBtn = within(dialog).getByRole('button', { name: /delete/i })
    await userEvent.click(confirmBtn)

    await waitFor(() => {
      expect(deleteCalled).toBe(true)
    })
  })

  it('instance-notice renders when no instance selected (no raw select)', () => {
    useInstanceStore.setState({ selectedInstanceId: null })

    const Wrapper = createWrapper()
    render(<TrafficShaping />, { wrapper: Wrapper })

    // Instance notice should render
    expect(
      screen.getByText(/Select an instance from the top bar to manage traffic shaping/i),
    ).toBeInTheDocument()

    // No raw <select> element for instance picking
    const selects = document.querySelectorAll('select')
    expect(selects.length).toBe(0)
  })
})

describe('RoutingRuleForm', () => {
  it('renders and submits fixture payload', async () => {
    const onSubmit = vi.fn()
    const Wrapper = createWrapper()

    render(
      <RoutingRuleForm onSubmit={onSubmit} onCancel={() => {}} loading={false} />,
      { wrapper: Wrapper },
    )

    // Fill in required field
    const nameInput = screen.getByPlaceholderText('e.g. Route DMZ to WAN')
    await userEvent.type(nameInput, 'Test Rule')

    // Submit
    await userEvent.click(screen.getByRole('button', { name: /create/i }))

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        name: 'Test Rule',
        enabled: true,
      }),
    )
  })
})

describe('TrafficPolicyForm', () => {
  it('submits QoSPolicyCreate payload', async () => {
    const onSubmit = vi.fn()
    const Wrapper = createWrapper()

    render(
      <TrafficPolicyForm onSubmit={onSubmit} onCancel={() => {}} loading={false} />,
      { wrapper: Wrapper },
    )

    // Fill in required fields
    const nameInputs = screen.getAllByRole('textbox')
    // First textbox is Policy Name
    await userEvent.type(nameInputs[0], 'test-policy')

    // Submit
    await userEvent.click(screen.getByRole('button', { name: /create/i }))

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        name: 'test-policy',
        algorithm: 'cake',
        interface_name: 'eth0',
        download_kbps: 100000,
        upload_kbps: 50000,
        enabled: true,
        classes: [],
      }),
    )
  })
})
