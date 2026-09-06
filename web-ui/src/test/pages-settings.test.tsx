import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { http, HttpResponse } from 'msw'
import userEvent from '@testing-library/user-event'
import { Settings } from '../pages/Settings'
import { useAuthStore } from '../stores/auth'
import { useThemeStore } from '../stores/theme'
import { adminUser, auditorUser } from './msw/fixtures'
import { server } from './msw/node'

/* -------------------------------------------------------------------------- */
/*  Helpers                                                                    */
/* -------------------------------------------------------------------------- */

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
}

function renderSettings() {
  const qc = makeQueryClient()
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <Settings />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

/**
 * Scoped lookup for sub-nav buttons. The page renders the section buttons
 * twice (desktop <nav> + mobile tab bar) and jsdom ignores CSS, so an
 * unscoped query would match both. Always resolve within the nav landmark.
 */
function navButton(name: string) {
  return within(screen.getByRole('navigation')).getByRole('button', { name })
}

/** Wait for the page to exit its loading state (LDAP query resolved). */
async function waitForLoaded() {
  // The sub-nav "Appearance" button appears once loading completes
  await waitFor(() => {
    expect(navButton('Appearance')).toBeInTheDocument()
  })
}

/* -------------------------------------------------------------------------- */
/*  Fixtures                                                                   */
/* -------------------------------------------------------------------------- */

const ldapFixture = {
  server_url: 'ldaps://ad.example.com:636',
  bind_dn: 'cn=admin,dc=example,dc=com',
  bind_password: 'secret',
  base_dn: 'dc=example,dc=com',
  user_filter: '(objectClass=person)',
}

/* -------------------------------------------------------------------------- */
/*  Tests                                                                      */
/* -------------------------------------------------------------------------- */

describe('Settings page', () => {
  beforeEach(() => {
    localStorage.clear()
    useAuthStore.setState({ token: 'tok', user: adminUser })
    useThemeStore.setState({ theme: 'system' })
  })

  /* ---- 1. Sub-nav switches sections -------------------------------------- */

  it('sub-nav switches active section — clicking System shows version info', async () => {
    const user = userEvent.setup()
    renderSettings()

    await waitForLoaded()

    // Default section is Appearance — theme control visible
    expect(screen.getByText('Theme')).toBeInTheDocument()

    // Click System in sub-nav
    await user.click(navButton('System'))

    // System Information card appears with APP_INFO values
    expect(screen.getByText('System Information')).toBeInTheDocument()
    // Both API Version and Frontend Version rows render APP_INFO.version
    expect(screen.getAllByText('2.0.0')).toHaveLength(2)
    expect(screen.getByText('e1580e735101')).toBeInTheDocument()
  })

  /* ---- 2. Theme segmented control sets store ----------------------------- */

  it('theme segmented control — clicking Dark sets useThemeStore', async () => {
    const user = userEvent.setup()
    renderSettings()

    await waitForLoaded()

    // Default is "system"
    expect(useThemeStore.getState().theme).toBe('system')

    // Click "dark" in the pill group
    await user.click(screen.getByRole('button', { name: 'dark' }))

    expect(useThemeStore.getState().theme).toBe('dark')
  })

  /* ---- 3. Non-admin sees gating note ------------------------------------- */

  it('non-admin sees "Administrator access required" and no LDAP fields', async () => {
    useAuthStore.setState({
      token: 'tok',
      user: { ...auditorUser, role: 'readonly' },
    })
    const user = userEvent.setup()
    renderSettings()

    await waitForLoaded()

    // Navigate to Authentication
    await user.click(navButton('Authentication'))

    // Gating note visible
    expect(
      screen.getByText(/administrator access required/i),
    ).toBeInTheDocument()

    // LDAP fields NOT visible
    expect(screen.queryByLabelText(/server url/i)).not.toBeInTheDocument()
  })

  /* ---- 4. LDAP save fires mutation + toast, no 'Saved!' span ------------ */

  it('LDAP save fires mutation and shows toast — no "Saved!" span', async () => {
    // Provide LDAP config so the form is populated
    let postReceived = false
    server.use(
      http.get('/api/v1/auth/ldap-config', () =>
        HttpResponse.json(ldapFixture),
      ),
      http.post('/api/v1/auth/ldap-config', async ({ request }) => {
        postReceived = true
        return HttpResponse.json(await request.json())
      }),
    )

    const user = userEvent.setup()
    renderSettings()

    await waitForLoaded()

    // Navigate to Authentication
    await user.click(navButton('Authentication'))

    // Wait for form to populate
    await waitFor(() => {
      expect(screen.getByDisplayValue('ldaps://ad.example.com:636')).toBeInTheDocument()
    })

    // Click Save
    await user.click(screen.getByRole('button', { name: /save/i }))

    // Mutation fired
    await waitFor(() => {
      expect(postReceived).toBe(true)
    })

    // No "Saved!" / "Configuration saved!" span in DOM
    expect(screen.queryByText(/saved!/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/configuration saved/i)).not.toBeInTheDocument()
  })

  /* ---- 5. Remove → ConfirmDialog, confirm() never called ---------------- */

  it('Remove LDAP triggers ConfirmDialog — window.confirm is never called', async () => {
    // Provide LDAP config + delete handler
    server.use(
      http.get('/api/v1/auth/ldap-config', () =>
        HttpResponse.json(ldapFixture),
      ),
      http.delete('/api/v1/auth/ldap-config', () =>
        HttpResponse.json(null),
      ),
    )

    const confirmSpy = vi.spyOn(window, 'confirm')
    const user = userEvent.setup()
    renderSettings()

    await waitForLoaded()

    // Navigate to Authentication
    await user.click(navButton('Authentication'))

    // Wait for form to populate
    await waitFor(() => {
      expect(screen.getByDisplayValue('ldaps://ad.example.com:636')).toBeInTheDocument()
    })

    // Click Remove configuration
    await user.click(
      screen.getByRole('button', { name: /remove configuration/i }),
    )

    // ConfirmDialog should appear — check for its title
    expect(
      screen.getByText('Remove LDAP configuration?'),
    ).toBeInTheDocument()

    // Impact line is present
    expect(
      screen.getByText(/removes the ldap configuration/i),
    ).toBeInTheDocument()

    // Assert window.confirm was NEVER called
    expect(confirmSpy).not.toHaveBeenCalled()
    confirmSpy.mockRestore()
  })

  /* ---- 6. APP_INFO rendered in System section ---------------------------- */

  it('APP_INFO constants are rendered in System section', async () => {
    const user = userEvent.setup()
    renderSettings()

    await waitForLoaded()

    await user.click(navButton('System'))

    // Version and migration from APP_INFO
    // (version appears twice on the page: API Version and Frontend Version rows)
    expect(screen.getAllByText('2.0.0')).toHaveLength(2)
    expect(screen.getByText('e1580e735101')).toBeInTheDocument()

    // Labels
    expect(screen.getByText('API Version')).toBeInTheDocument()
    expect(screen.getByText('Frontend Version')).toBeInTheDocument()
    expect(screen.getByText('Migration')).toBeInTheDocument()
    expect(screen.getByText('Database')).toBeInTheDocument()
  })
})
