import { describe, expect, it } from 'vitest'
import { render, screen, waitFor, fireEvent, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { http, HttpResponse } from 'msw'
import { server } from './msw/node'
import { useAuthStore } from '../stores/auth'
import { users, auditLogs } from './msw/fixtures'
import { Users } from '../pages/Users'
import { AuditLogs } from '../pages/AuditLogs'
import type { AuditLog } from '../types'

/* -------------------------------------------------------------------------- */
/*  Helpers                                                                    */
/* -------------------------------------------------------------------------- */

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

/* -------------------------------------------------------------------------- */
/*  Users page                                                                 */
/* -------------------------------------------------------------------------- */

describe('Users', () => {
  it('toggle active opens ConfirmDialog before firing mutation', async () => {
    let patchBody: Record<string, unknown> | null = null
    server.use(
      http.patch('/api/v1/users/:id', async ({ request }) => {
        patchBody = await request.json() as Record<string, unknown>
        return HttpResponse.json({ ...users[0], is_active: false })
      }),
    )

    const Wrapper = createWrapper()
    render(<Users />, { wrapper: Wrapper })

    await screen.findByText('admin')

    // Click the Switch to toggle active
    const toggle = screen.getByRole('switch', { name: /toggle active for admin/i })
    fireEvent.click(toggle)

    // ConfirmDialog should appear with warning variant
    const dialog = await screen.findByRole('dialog')
    expect(within(dialog).getByText(/deactivate user/i)).toBeInTheDocument()
    expect(within(dialog).getByText(/changes whether admin can sign in/i)).toBeInTheDocument()

    // Click Deactivate
    await userEvent.click(within(dialog).getByRole('button', { name: /deactivate/i }))

    await waitFor(() => {
      expect(patchBody).not.toBeNull()
      expect(patchBody).toMatchObject({ is_active: false })
    })
  })

  it('delete opens danger ConfirmDialog and fires mutation on confirm', async () => {
    let deleteCalled = false
    server.use(
      http.delete('/api/v1/users/:id', () => {
        deleteCalled = true
        return new HttpResponse(null, { status: 204 })
      }),
    )

    const Wrapper = createWrapper()
    render(<Users />, { wrapper: Wrapper })

    await screen.findByText('admin')

    // Open kebab menu for first user
    const kebab = screen.getAllByRole('button', { name: /user actions/i })[0]
    await userEvent.click(kebab)

    // Click Delete
    await userEvent.click(screen.getByText('Delete'))

    // ConfirmDialog should appear
    const dialog = await screen.findByRole('dialog')
    expect(within(dialog).getByText(/delete user/i)).toBeInTheDocument()
    expect(within(dialog).getByText(/permanently removes/i)).toBeInTheDocument()

    // Confirm
    await userEvent.click(within(dialog).getByRole('button', { name: /^delete$/i }))

    await waitFor(() => {
      expect(deleteCalled).toBe(true)
    })
  })
})

/* -------------------------------------------------------------------------- */
/*  AuditLogs page                                                             */
/* -------------------------------------------------------------------------- */

describe('AuditLogs', () => {
  it('pagination footer renders with pageSize 25', async () => {
    // Ensure admin
    useAuthStore.setState({ token: 'test', user: { id: 1, username: 'admin', email: 'a@b.c', role: 'admin' } })

    const Wrapper = createWrapper()
    render(<AuditLogs />, { wrapper: Wrapper })

    await screen.findByText('vpn.server.update on vpn_server #1')

    // Pagination footer present
    expect(screen.getByText(/rows per page/i)).toBeInTheDocument()

    // pageSize 25 should be the active page-size select value
    const pageSizeSelect = screen.getAllByRole('combobox').find((el) =>
      Array.from((el as HTMLSelectElement).options).map((o) => o.value).includes('25'),
    ) as HTMLSelectElement
    expect(pageSizeSelect).toBeTruthy()
    expect(pageSizeSelect.value).toBe('25')
  })

  it('date filter narrows rows', async () => {
    useAuthStore.setState({ token: 'test', user: { id: 1, username: 'admin', email: 'a@b.c', role: 'admin' } })

    const dateFixtures: AuditLog[] = [
      { id: 10, user_id: 1, instance_id: null, action: 'auth.login', resource_type: 'user', resource_id: '1', old_value: null, new_value: null, ip_address: '10.0.0.1', timestamp: '2026-01-10T09:00:00.000Z' },
      { id: 11, user_id: 1, instance_id: null, action: 'firewall.rule.create', resource_type: 'firewall_rule', resource_id: '5', old_value: null, new_value: { name: 'test' }, ip_address: '10.0.0.1', timestamp: '2026-01-15T14:30:00.000Z' },
      { id: 12, user_id: 1, instance_id: null, action: 'user.update', resource_type: 'user', resource_id: '2', old_value: { role: 'user' }, new_value: { role: 'admin' }, ip_address: '10.0.0.1', timestamp: '2026-01-20T18:00:00.000Z' },
    ]

    server.use(
      http.get('/api/v1/audit/logs', () => HttpResponse.json(dateFixtures)),
    )

    const Wrapper = createWrapper()
    render(<AuditLogs />, { wrapper: Wrapper })

    await screen.findByText('auth.login on user #1')

    // All 3 rows visible initially
    expect(screen.getByText('firewall.rule.create on firewall_rule #5')).toBeInTheDocument()
    expect(screen.getByText('user.update on user #2')).toBeInTheDocument()

    // Set date from = 2026-01-12 → should remove the Jan 10 row
    const dateFrom = screen.getByLabelText(/date from/i)
    fireEvent.change(dateFrom, { target: { value: '2026-01-12' } })

    // auth.login row should disappear (its date is Jan 10, before Jan 12)
    await waitFor(() => {
      expect(screen.queryByText('auth.login on user #1')).not.toBeInTheDocument()
    })

    // The other two should still be there
    expect(screen.getByText('firewall.rule.create on firewall_rule #5')).toBeInTheDocument()
    expect(screen.getByText('user.update on user #2')).toBeInTheDocument()
  })

  it('resolves user names and shows fallback for deleted user', async () => {
    useAuthStore.setState({ token: 'test', user: { id: 1, username: 'admin', email: 'a@b.c', role: 'admin' } })

    const fixturesWithDeleted: AuditLog[] = [
      { id: 20, user_id: 1, instance_id: 1, action: 'auth.login', resource_type: 'user', resource_id: '1', old_value: null, new_value: null, ip_address: '10.0.0.1', timestamp: '2026-01-05T10:00:00.000Z' },
      { id: 21, user_id: 99, instance_id: null, action: 'user.delete', resource_type: 'user', resource_id: '99', old_value: { username: 'ghost' }, new_value: null, ip_address: '10.0.0.1', timestamp: '2026-01-05T10:05:00.000Z' },
    ]

    server.use(
      http.get('/api/v1/audit/logs', () => HttpResponse.json(fixturesWithDeleted)),
    )

    const Wrapper = createWrapper()
    render(<AuditLogs />, { wrapper: Wrapper })

    // Known user_id=1 resolves to "admin" from the users hook
    await screen.findByText('admin')
    // The cell "admin" from the user column should be visible (distinct from PageHeader text)

    // Deleted user_id=99 shows fallback format
    expect(screen.getByText('User #99 (unknown)')).toBeInTheDocument()
  })

  it('non-admin shows Access Denied EmptyState', async () => {
    useAuthStore.setState({ token: 'test', user: { id: 2, username: 'viewer', email: 'v@b.c', role: 'readonly' } })

    const Wrapper = createWrapper()
    render(<AuditLogs />, { wrapper: Wrapper })

    expect(await screen.findByText('Access Denied')).toBeInTheDocument()
    expect(screen.getByText(/admin privileges/i)).toBeInTheDocument()
  })

  it('search filters rows', async () => {
    useAuthStore.setState({ token: 'test', user: { id: 1, username: 'admin', email: 'a@b.c', role: 'admin' } })

    const Wrapper = createWrapper()
    render(<AuditLogs />, { wrapper: Wrapper })

    await screen.findByText('vpn.server.update on vpn_server #1')

    // Type in DataTable search
    const searchInput = screen.getByRole('textbox', { name: /search/i })
    await userEvent.type(searchInput, 'firewall')

    // Only the firewall rule row should remain (search matches the action string)
    await waitFor(() => {
      expect(screen.queryByText('vpn.server.update on vpn_server #1')).not.toBeInTheDocument()
    })
    expect(screen.getByText('firewall.rule.create on firewall_rule #3')).toBeInTheDocument()
  })
})


