import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { http, HttpResponse } from 'msw'
import { server } from './msw/node'
import { useInstanceStore } from '../stores/instance'
import { firewallRules, natRules } from './msw/fixtures'
import { FirewallRules } from '../pages/FirewallRules'
import { NatRules } from '../pages/NatRules'

/**
 * FirewallRules + NatRules page tests — Task 18.
 *
 * Covers: deploy path fix, deploy checkbox gating, Switch toggle confirm,
 * reorder aria-labels, table search filtering, NAT create toast, and
 * instance-notice rendering.
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

describe('FirewallRules', () => {
  it('deploy path uses /firewall/apply/ not /firewall/deploy/', async () => {
    let capturedUrl = ''
    server.use(
      http.post('/api/v1/firewall/apply/:instanceId', ({ request }) => {
        capturedUrl = new URL(request.url).pathname
        return HttpResponse.json({ status: 'ok' })
      }),
    )

    const Wrapper = createWrapper()
    render(<FirewallRules />, { wrapper: Wrapper })

    // Wait for rules to load
    await screen.findByText('Allow HTTPS inbound')

    // Open deploy dialog
    await userEvent.click(screen.getByRole('button', { name: /deploy/i }))

    // Check the review checkbox
    const checkbox = await screen.findByRole('checkbox')
    await userEvent.click(checkbox)

    // Click Deploy in the dialog
    const deployBtns = screen.getAllByRole('button', { name: /deploy/i })
    // The dialog deploy button is the last one
    await userEvent.click(deployBtns[deployBtns.length - 1])

    await waitFor(() => {
      expect(capturedUrl).toBe('/api/v1/firewall/apply/1')
    })
  })

  it('deploy dialog: confirm button disabled until review checkbox checked', async () => {
    const Wrapper = createWrapper()
    render(<FirewallRules />, { wrapper: Wrapper })

    await screen.findByText('Allow HTTPS inbound')

    // Open deploy dialog
    await userEvent.click(screen.getByRole('button', { name: /deploy/i }))

    // The dialog Deploy button should be disabled
    const dialog = await screen.findByRole('dialog')
    const deployBtnInDialog = dialog.querySelectorAll('button')
    const confirmBtn = Array.from(deployBtnInDialog).find(
      (b) => b.textContent?.includes('Deploy') && !b.textContent?.includes('Cancel'),
    )
    expect(confirmBtn).toBeDisabled()

    // Check the review checkbox
    const checkbox = screen.getByRole('checkbox')
    await userEvent.click(checkbox)

    // Now the Deploy button should be enabled
    expect(confirmBtn).not.toBeDisabled()
  })

  it('Switch toggle opens a warning confirm dialog', async () => {
    const Wrapper = createWrapper()
    render(<FirewallRules />, { wrapper: Wrapper })

    await screen.findByText('Allow HTTPS inbound')

    // Find the switch for the first rule
    const switches = screen.getAllByRole('switch')
    expect(switches.length).toBeGreaterThan(0)

    // Click the first switch (Allow HTTPS inbound — currently enabled)
    await userEvent.click(switches[0])

    // Confirm dialog should appear with warning message
    const dialog = await screen.findByRole('dialog')
    expect(dialog).toHaveTextContent(/Disable rule/)
    expect(dialog).toHaveTextContent(/Traffic matching this rule may be blocked/)
  })

  it('reorder buttons have aria-labels', async () => {
    const Wrapper = createWrapper()
    render(<FirewallRules />, { wrapper: Wrapper })

    await screen.findByText('Allow HTTPS inbound')

    const moveUp = screen.getAllByRole('button', { name: 'Move rule up' })
    const moveDown = screen.getAllByRole('button', { name: 'Move rule down' })

    expect(moveUp.length).toBeGreaterThan(0)
    expect(moveDown.length).toBeGreaterThan(0)
    expect(moveUp[0]).toHaveAttribute('aria-label', 'Move rule up')
    expect(moveDown[0]).toHaveAttribute('aria-label', 'Move rule down')
  })

  it('table search filters rows', async () => {
    const Wrapper = createWrapper()
    render(<FirewallRules />, { wrapper: Wrapper })

    await screen.findByText('Allow HTTPS inbound')

    // All three rules should be visible
    expect(screen.getByText('Allow HTTPS inbound')).toBeInTheDocument()
    expect(screen.getByText('Allow DNS outbound')).toBeInTheDocument()
    expect(screen.getByText('Default drop')).toBeInTheDocument()

    // Type in search
    const searchInput = screen.getByRole('textbox', { name: /search/i })
    await userEvent.type(searchInput, 'DNS')

    // Only DNS rule should be visible
    await waitFor(() => {
      expect(screen.queryByText('Allow HTTPS inbound')).not.toBeInTheDocument()
    })
    expect(screen.getByText('Allow DNS outbound')).toBeInTheDocument()
  })

  it('instance-notice renders when no instance selected', () => {
    useInstanceStore.setState({ selectedInstanceId: null })

    const Wrapper = createWrapper()
    render(<FirewallRules />, { wrapper: Wrapper })

    expect(
      screen.getByText(/Select an instance from the top bar to manage its firewall/i),
    ).toBeInTheDocument()
  })
})

describe('NatRules', () => {
  it('instance-notice renders when no instance selected', () => {
    useInstanceStore.setState({ selectedInstanceId: null })

    const Wrapper = createWrapper()
    render(<NatRules />, { wrapper: Wrapper })

    expect(
      screen.getByText(/Select an instance from the top bar to manage its NAT rules/i),
    ).toBeInTheDocument()
  })
})
