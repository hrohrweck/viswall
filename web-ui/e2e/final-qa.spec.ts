import { expect, test, type Page } from '@playwright/test'
import { execSync } from 'node:child_process'
import * as fs from 'node:fs'
import * as path from 'node:path'
import { seedAuthSession, seedInstanceState } from './helpers/auth'

/**
 * F3 final QA interaction sweep: drives the redesigned app end-to-end on the
 * MSW-seeded harness and asserts the headline behaviours with real
 * visible-text / role / URL assertions (no expect(true)).
 *
 * The firewall-deploy success path needs a 2xx for POST
 * /api/v1/firewall/apply/:id, which the read-only MSW fixture set does not
 * mock — the worker's onUnhandledRequest:'bypass' passes it through, so the
 * spec fulfills it via page.route (network-level, no app code involved).
 *
 * ErrorBoundary/QueryError via an MSW override route is intentionally
 * skipped: the browser worker is not exposed on window, so a spec cannot
 * worker.use() an override, and page.route cannot intercept GETs the worker
 * already answered — forcing it would require product-file changes.
 */

// Unset theme resolves to 'system'; pin emulation so light/dark assertions
// and the theme-toggle accessible names are deterministic.
test.use({ colorScheme: 'light' })

function shotsDir(): string {
  // Worktrees report the MAIN repo's .git dir — screenshots land in the
  // main checkout's .omo/evidence (same convention as a11y.spec.ts).
  const gitDir = execSync('git rev-parse --path-format=absolute --git-common-dir')
    .toString()
    .trim()
  return path.join(path.resolve(gitDir, '..'), '.omo', 'evidence', 'frontend-redesign', 'final-qa')
}

async function shot(page: Page, name: string): Promise<void> {
  const dir = shotsDir()
  await fs.promises.mkdir(dir, { recursive: true })
  await page.screenshot({ path: path.join(dir, `${name}.png`), fullPage: true })
}

async function signInAndGo(page: Page, route: string, opts?: { instance?: boolean }): Promise<void> {
  await seedAuthSession(page)
  if (opts?.instance) await seedInstanceState(page)
  await page.goto(route)
  await page.waitForLoadState('networkidle')
  await expect(page.locator('#main-content')).toBeVisible()
}

/* ------------------------------------------------------------------ */
/*  Login                                                              */
/* ------------------------------------------------------------------ */

// REAL PRODUCT BUG (captured F3, fix must land in product code): the axios
// 401 interceptor in src/utils/api.ts unconditionally does
// window.location.href = '/login' — including for the login endpoint's own
// invalid-credentials 401 — so the page reloads before the error banner
// paints. Probe evidence: banner never becomes visible; framenavigated
// fires twice for /login; the jsdom RTL login-error test passes only
// because jsdom ignores location assignments. Remove .fixme and assert the
// banner once the interceptor skips the auth endpoints.
test.fixme('login: invalid credentials → error banner, stays on /login', async ({ page }) => {
  await page.goto('/login')
  await page.waitForLoadState('networkidle')

  await page.locator('input[type="text"]').fill('admin')
  await page.locator('input[type="password"]').fill('definitely-wrong')
  await page.getByRole('button', { name: 'Sign In' }).click()

  const banner = page.getByRole('alert')
  await expect(banner).toBeVisible()
  await expect(banner).toContainText('Invalid credentials')
  await expect(page).toHaveURL(/\/login/)

  await shot(page, '01-login-error-banner')
})

test('login: valid credentials → lands on dashboard', async ({ page }) => {
  await page.goto('/login')
  await page.waitForLoadState('networkidle')

  await page.locator('input[type="text"]').fill('admin')
  await page.locator('input[type="password"]').fill('admin')
  await page.getByRole('button', { name: 'Sign In' }).click()

  await expect(page).toHaveURL(/\/$/)
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible()
})

/* ------------------------------------------------------------------ */
/*  Dashboard                                                          */
/* ------------------------------------------------------------------ */

test('dashboard: stat cards render and instance-health table lists all 3 instances', async ({
  page,
}) => {
  await signInAndGo(page, '/')

  for (const label of ['Total instances', 'Firewall rules', 'VPN servers', 'Mail domains']) {
    await expect(page.locator('#main-content').getByText(label, { exact: true })).toBeVisible()
  }

  // Scope to the table — instance names also appear in the "Attention
  // needed" card and the top-bar switcher (strict-mode collision).
  const healthTable = page.getByRole('table')
  await expect(healthTable.getByText('edge-berlin-01')).toBeVisible({ timeout: 15_000 })
  await expect(healthTable.getByText('edge-oslo-02')).toBeVisible()
  await expect(healthTable.getByText('edge-vie-03')).toBeVisible()

  await shot(page, '02-dashboard')
})

/* ------------------------------------------------------------------ */
/*  Sidebar                                                            */
/* ------------------------------------------------------------------ */

test('sidebar: groups render, collapse → rail, expand restores', async ({ page }) => {
  await signInAndGo(page, '/')

  const sidebar = page.locator('aside')
  for (const label of ['Overview', 'Network', 'Services', 'Administration']) {
    await expect(sidebar.getByText(label, { exact: true })).toBeVisible()
  }

  await sidebar.getByRole('button', { name: 'Collapse sidebar' }).click()
  await expect(sidebar.getByText('Dashboard')).not.toBeVisible()
  await expect(sidebar.getByRole('button', { name: 'Expand sidebar' })).toBeVisible()

  await sidebar.getByRole('button', { name: 'Expand sidebar' }).click()
  await expect(sidebar.getByText('Dashboard')).toBeVisible()
})

test('sidebar: mobile viewport (390px) hamburger → drawer → scrim close', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await signInAndGo(page, '/')

  const hamburger = page.getByRole('button', { name: 'Open navigation' })
  await expect(hamburger).toBeVisible({ timeout: 15_000 })

  const drawer = page.locator('.fixed.inset-y-0')
  await expect(drawer).toHaveClass(/translate-x-\[-100%\]/)

  await hamburger.click()
  await expect(drawer).toHaveClass(/translate-x-0/)
  await expect(page.locator('aside').getByText('Dashboard')).toBeVisible()

  const scrim = page.locator('[data-testid="sidebar-scrim"]')
  await expect(scrim).toBeVisible()
  await shot(page, '03-mobile-drawer')

  // Click right side of the scrim, away from the 256px drawer.
  await scrim.click({ position: { x: 350, y: 400 } })
  await expect(drawer).toHaveClass(/translate-x-\[-100%\]/)
})

/* ------------------------------------------------------------------ */
/*  Command palette                                                    */
/* ------------------------------------------------------------------ */

test('command palette: ⌘K → "vpn" → Enter → /vpn', async ({ page }) => {
  await signInAndGo(page, '/')

  await page.keyboard.press('ControlOrMeta+k')
  const input = page.getByPlaceholder('Search pages, instances, actions…')
  await expect(input).toBeVisible()

  await input.fill('vpn')
  await expect(page.locator('[cmdk-item]').filter({ hasText: 'VPN' }).first()).toBeVisible()
  await shot(page, '01-command-palette')

  await page.keyboard.press('Enter')
  await expect(page).toHaveURL(/\/vpn$/)
  await expect(page.getByRole('heading', { name: 'VPN Servers' })).toBeVisible()
})

/* ------------------------------------------------------------------ */
/*  Theme toggle                                                       */
/* ------------------------------------------------------------------ */

test('theme: toggle flips html.dark and back', async ({ page }) => {
  await page.addInitScript(() => window.localStorage.setItem('viswall-theme', 'light'))
  await signInAndGo(page, '/')

  await expect(page.locator('html')).not.toHaveClass(/\bdark\b/)

  // light → dark
  await page.getByRole('button', { name: 'Theme: light' }).click()
  await expect(page.locator('html')).toHaveClass(/\bdark\b/)

  // dark → system (resolves to light under pinned light emulation)
  await page.getByRole('button', { name: 'Theme: dark' }).click()
  await expect(page.locator('html')).not.toHaveClass(/\bdark\b/)
})

/* ------------------------------------------------------------------ */
/*  Firewall                                                           */
/* ------------------------------------------------------------------ */

test('firewall: deploy dialog gated by review checkbox, confirm → success toast', async ({
  page,
}) => {
  // MSW has no write handlers — the bypassed POST is fulfilled at the
  // network layer so the success toast path can be asserted.
  await page.route('**/api/v1/firewall/apply/*', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: '{"status": "ok"}' }),
  )
  await signInAndGo(page, '/firewall', { instance: true })

  await expect(page.getByRole('table').getByText('Allow HTTPS inbound')).toBeVisible({
    timeout: 15_000,
  })

  await page.getByRole('button', { name: 'Deploy', exact: true }).click()

  const dialog = page.getByRole('dialog')
  await expect(dialog).toBeVisible()
  await expect(dialog.getByRole('heading', { name: 'Deploy Firewall Rules' })).toBeVisible()
  await expect(dialog.getByText('3 rules')).toBeVisible() // 3 fixture rules

  // Confirm stays disabled until the review checkbox is checked.
  const confirm = dialog.getByRole('button', { name: 'Deploy' })
  await expect(confirm).toBeDisabled()
  await dialog.locator('#deploy-reviewed').check()
  await expect(confirm).toBeEnabled()

  await shot(page, '04-firewall-deploy-dialog')

  await confirm.click()
  const toast = page.locator('[data-sonner-toast]').filter({ hasText: 'Firewall rules deployed' })
  await expect(toast.first()).toBeVisible()
  await expect(dialog).not.toBeVisible()
})

test('firewall: rule enable Switch opens confirm dialog, cancel leaves state', async ({ page }) => {
  await signInAndGo(page, '/firewall', { instance: true })

  const toggle = page.getByRole('switch', { name: 'Disable rule Allow HTTPS inbound' })
  await expect(toggle).toBeVisible({ timeout: 15_000 })
  await expect(toggle).toHaveAttribute('data-state', 'checked')

  await toggle.click()
  const dialog = page.getByRole('dialog')
  await expect(dialog).toBeVisible()
  await expect(dialog.getByRole('heading', { name: 'Disable Rule' })).toBeVisible()
  await expect(dialog.getByText(/Allow HTTPS inbound/)).toBeVisible()

  await dialog.getByRole('button', { name: 'Cancel' }).click()
  await expect(dialog).not.toBeVisible()
  await expect(toggle).toHaveAttribute('data-state', 'checked')
})

test('firewall: table search filters rows', async ({ page }) => {
  await signInAndGo(page, '/firewall', { instance: true })

  const table = page.getByRole('table')
  await expect(table.getByText('Allow HTTPS inbound')).toBeVisible({ timeout: 15_000 })

  await page.getByPlaceholder('Search rules…').fill('HTTPS')

  await expect(table.getByText('Default drop')).not.toBeVisible()
  await expect(table.getByText('Allow DNS outbound')).not.toBeVisible()
  await expect(table.locator('tbody tr')).toHaveCount(1)
  await expect(table.getByText('Allow HTTPS inbound')).toBeVisible()
})

/* ------------------------------------------------------------------ */
/*  QoS                                                                */
/* ------------------------------------------------------------------ */

test('qos: delete opens confirm, cancel leaves the policy', async ({ page }) => {
  await signInAndGo(page, '/traffic', { instance: true })

  await expect(page.getByText('wan-shaping')).toBeVisible({ timeout: 15_000 })

  await page.getByRole('button', { name: 'Delete policy' }).click()
  const dialog = page.getByRole('dialog')
  await expect(dialog).toBeVisible()
  await expect(dialog.getByRole('heading', { name: 'Delete QoS Policy' })).toBeVisible()
  await expect(dialog.getByText(/wan-shaping/)).toBeVisible()

  await dialog.getByRole('button', { name: 'Cancel' }).click()
  await expect(dialog).not.toBeVisible()
  await expect(page.getByText('wan-shaping')).toBeVisible()
})

/* ------------------------------------------------------------------ */
/*  VPN detail                                                         */
/* ------------------------------------------------------------------ */

test('vpn detail: Stop confirm shows impact with live client count', async ({ page }) => {
  await signInAndGo(page, '/vpn/servers/1', { instance: true })

  await expect(page.getByRole('heading', { name: 'wg-site-a' })).toBeVisible({ timeout: 15_000 })

  await page.getByRole('button', { name: 'Stop', exact: true }).click()
  const dialog = page.getByRole('dialog')
  await expect(dialog).toBeVisible()
  await expect(dialog.getByRole('heading', { name: 'Stop VPN Server' })).toBeVisible()
  // 2 fixture clients are attached to server 1 — the impact line must
  // carry the live count, not a placeholder.
  await expect(dialog.getByText('Disconnects 2 connected clients.')).toBeVisible()

  await dialog.getByRole('button', { name: 'Cancel' }).click()
  await expect(dialog).not.toBeVisible()
})

/* ------------------------------------------------------------------ */
/*  Mail wizard                                                        */
/* ------------------------------------------------------------------ */

test('mail: wizard reaches Review showing entered domain, cancels without creating', async ({
  page,
}) => {
  await signInAndGo(page, '/mail/domains/create', { instance: true })

  // Step 1 — Domain
  await page.getByRole('textbox').fill('final-qa.test')
  await page.getByRole('button', { name: 'Continue' }).click()

  // Step 2 — Security (toggles for SpamAssassin/ClamAV/DKIM/…)
  await expect(page.getByText('Configure security features for this domain:')).toBeVisible()
  await page.getByRole('button', { name: 'Continue' }).click()

  // Step 3 — Review shows the entered domain before submit
  await expect(page.getByRole('heading', { name: 'Review configuration' })).toBeVisible()
  await shot(page, '05-mail-review-step')
  await expect(page.getByText('final-qa.test', { exact: true })).toBeVisible()

  // Back out and cancel — no create call is fired.
  await page.getByRole('button', { name: 'Back' }).click()
  await page.getByRole('button', { name: 'Back' }).click()
  await page.getByRole('button', { name: 'Cancel' }).click()
  await expect(page).toHaveURL(/\/mail$/)
  await expect(page.getByRole('heading', { name: 'Mail Domains' })).toBeVisible()
})

/* ------------------------------------------------------------------ */
/*  Users                                                              */
/* ------------------------------------------------------------------ */

test('users: active toggle opens confirm with impact, cancel', async ({ page }) => {
  await signInAndGo(page, '/users')

  const toggle = page.getByRole('switch', { name: 'Toggle active for admin' })
  await expect(toggle).toBeVisible({ timeout: 15_000 })

  await toggle.click()
  const dialog = page.getByRole('dialog')
  await expect(dialog).toBeVisible()
  await expect(dialog.getByRole('heading', { name: 'Deactivate User' })).toBeVisible()
  await expect(dialog.getByText('Changes whether admin can sign in.')).toBeVisible()

  await dialog.getByRole('button', { name: 'Cancel' }).click()
  await expect(dialog).not.toBeVisible()
  await expect(toggle).toHaveAttribute('data-state', 'checked')
})

/* ------------------------------------------------------------------ */
/*  Audit logs                                                         */
/* ------------------------------------------------------------------ */

test('audit: pagination footer, date-filter inputs, resolved usernames', async ({ page }) => {
  await signInAndGo(page, '/audit')

  const table = page.getByRole('table')
  await expect(table).toBeVisible({ timeout: 15_000 })

  // Pagination footer
  await expect(page.getByText('Rows per page')).toBeVisible()
  await expect(page.getByText('1–3 of 3')).toBeVisible()

  // Date filter inputs
  await expect(page.getByLabel('Date from')).toBeVisible()
  await expect(page.getByLabel('Date to')).toBeVisible()

  // user_id 1 resolved to the fixture username in every row — none of the
  // rows falls back to "User #1 (unknown)".
  await expect(table.getByText('admin', { exact: true })).toHaveCount(3)
  // Summary of the newest fixture entry
  await expect(table.getByText(/vpn\.server\.update/)).toBeVisible()

  await shot(page, '06-audit-logs')
})

/* ------------------------------------------------------------------ */
/*  Instance switcher (top bar)                                        */
/* ------------------------------------------------------------------ */

test('instance switcher: switching instance updates the trigger label', async ({ page }) => {
  await signInAndGo(page, '/')

  const header = page.locator('header')
  const trigger = header.getByRole('button').filter({ hasText: 'Select instance' })
  await expect(trigger).toBeVisible()

  await trigger.click()
  const oslo = page.getByRole('menuitem').filter({ hasText: 'edge-oslo-02' })
  await expect(oslo).toBeVisible()
  await oslo.click()

  await expect(header.getByText('edge-oslo-02')).toBeVisible()
  await expect(trigger).not.toBeVisible()
})
