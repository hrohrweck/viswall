import { beforeEach, describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { Login } from '../pages/Login'
import { useAuthStore } from '../stores/auth'
import { loginResponse, validCredentials } from './msw/fixtures'

/**
 * RTL smoke test for the QA harness: proves React Testing Library renders,
 * user-event drives the form, and the MSW node server answers
 * POST /api/v1/auth/login with the deterministic fixture set.
 *
 * The Login page labels are not programmatically associated with their
 * inputs (pre-existing markup), so the fields are selected by type.
 */
function renderLogin() {
  const utils = render(
    <MemoryRouter>
      <Login />
    </MemoryRouter>,
  )
  const username = utils.container.querySelector<HTMLInputElement>('input[type="text"]')!
  const password = utils.container.querySelector<HTMLInputElement>('input[type="password"]')!
  return { ...utils, username, password }
}

describe('MSW + RTL smoke', () => {
  beforeEach(() => {
    localStorage.clear()
    useAuthStore.setState({ token: null, user: null })
  })

  it('renders the login page', () => {
    renderLogin()
    expect(screen.getByRole('heading', { name: 'Viswall' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('logs in with fixture credentials via the MSW node server', async () => {
    const user = userEvent.setup()
    const { username, password } = renderLogin()

    await user.type(username, validCredentials.username)
    await user.type(password, validCredentials.password)
    await user.click(screen.getByRole('button', { name: /sign in/i }))
    await screen.findByRole('button', { name: 'Sign In' })

    const { token, user: authed } = useAuthStore.getState()
    expect(token).toBe(loginResponse.access_token)
    expect(authed?.username).toBe(loginResponse.user.username)

    const persisted = JSON.parse(localStorage.getItem('viswall-auth') ?? '{}') as {
      state?: { token?: string }
    }
    expect(persisted.state?.token).toBe(loginResponse.access_token)
  })

  it('shows the API error for rejected credentials', async () => {
    const user = userEvent.setup()
    const { username, password } = renderLogin()

    await user.type(username, 'admin')
    await user.type(password, 'wrong-password')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    expect(await screen.findByText('Invalid credentials')).toBeInTheDocument()
    expect(useAuthStore.getState().token).toBeNull()
  })
})
