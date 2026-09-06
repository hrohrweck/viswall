import { beforeEach, describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Login } from '../pages/Login'
import { useAuthStore } from '../stores/auth'
import { loginResponse, validCredentials } from './msw/fixtures'

/**
 * RTL smoke test for the QA harness: proves React Testing Library renders,
 * user-event drives the form, and the MSW node server answers
 * POST /api/v1/auth/login with the deterministic fixture set.
 *
 * The Login page now uses kit Field/Label for accessible input association
 * and useLogin mutation hook for the auth flow.
 */
function makeQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
}

function renderLogin() {
  const qc = makeQueryClient()
  const utils = render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <Login />
      </MemoryRouter>
    </QueryClientProvider>,
  )
  return { ...utils, qc }
}

describe('MSW + RTL smoke', () => {
  beforeEach(() => {
    localStorage.clear()
    useAuthStore.setState({ token: null, user: null })
  })

  it('renders the login page', () => {
    renderLogin()
    expect(screen.getByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('logs in with fixture credentials via the MSW node server', async () => {
    const user = userEvent.setup()
    renderLogin()

    await user.type(screen.getByLabelText(/username/i), validCredentials.username)
    await user.type(screen.getByLabelText(/password/i), validCredentials.password)
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    const { token, user: authed } = useAuthStore.getState()
    expect(token).toBe(loginResponse.access_token)
    expect(authed?.username).toBe(loginResponse.user.username)
  })

  it('shows the API error for rejected credentials', async () => {
    const user = userEvent.setup()
    renderLogin()

    await user.type(screen.getByLabelText(/username/i), 'admin')
    await user.type(screen.getByLabelText(/password/i), 'wrong-password')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    expect(await screen.findByText('Invalid credentials')).toBeInTheDocument()
    expect(useAuthStore.getState().token).toBeNull()
  })
})
