import { beforeEach, describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { useInstanceStore } from '../stores/instance'
import { useAuthStore } from '../stores/auth'
import { Interfaces } from '../pages/Interfaces'

/**
 * Interfaces page tests — host interface management.
 *
 * Covers: instance notice, configured-interfaces table, live-state
 * discovery via the node agent, and the apply flow with result card.
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
  useAuthStore.setState({
    token: 'test-token',
    user: { id: 1, username: 'admin', email: 'admin@example.com', role: 'superadmin' },
  })
})

describe('Interfaces', () => {
  it('prompts for instance selection when none selected', () => {
    useInstanceStore.setState({ selectedInstanceId: null })

    const Wrapper = createWrapper()
    render(<Interfaces />, { wrapper: Wrapper })

    expect(
      screen.getByText(/select an instance from the top bar/i),
    ).toBeInTheDocument()
  })

  it('lists configured interfaces', async () => {
    const Wrapper = createWrapper()
    render(<Interfaces />, { wrapper: Wrapper })

    expect(await screen.findByText('wan0')).toBeInTheDocument()
    expect(screen.getByText('lan0')).toBeInTheDocument()
    // Static config details are shown
    expect(screen.getByText(/203\.0\.113\.10\/255\.255\.255\.0/)).toBeInTheDocument()
    // The persisted static role badge
    expect(screen.getAllByText('wan').length).toBeGreaterThanOrEqual(1)
  })

  it('discovers live host state on demand', async () => {
    const Wrapper = createWrapper()
    render(<Interfaces />, { wrapper: Wrapper })

    // Placeholder until the user asks for live state
    expect(screen.getByText(/query the node agent/i)).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: /discover/i }))

    expect(await screen.findByText(/bc:24:11:2f:a1:01/)).toBeInTheDocument()
    expect(screen.getByText('default route')).toBeInTheDocument()
    expect(screen.getByText(/GW 203\.0\.113\.1/)).toBeInTheDocument()
  })

  it('applies configuration and shows the result', async () => {
    const Wrapper = createWrapper()
    render(<Interfaces />, { wrapper: Wrapper })

    await userEvent.click(screen.getByRole('button', { name: /apply to host/i }))
    await userEvent.click(screen.getByRole('button', { name: 'Apply' }))

    // Result card renders the agent's report
    expect(await screen.findByText('Last Apply Result')).toBeInTheDocument()
    expect(screen.getByText('interface configuration applied')).toBeInTheDocument()
    expect(screen.getByText(/persisted to \/etc\/netplan\/60-viswall\.yaml/i)).toBeInTheDocument()
  })
})
