import { test, expect, type Page } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
import { execSync } from 'node:child_process'
import * as fs from 'node:fs'
import * as path from 'node:path'
import { seedAuthSession, seedInstanceState } from './helpers/auth'

/**
 * Full-route axe sweep (todo 30): every router path, both themes, zero
 * serious/critical violations allowed. Doubles as the F3 pre-run — the
 * route list below MUST stay in sync with src/router.tsx.
 *
 * color-contrast is ENABLED (the token layer from todo 2 was
 * contrast-checked; the legacy disable in e2e/axe.ts predates it).
 */

interface RouteSpec {
  path: string
  label: string
  auth: boolean
}

const ROUTES: RouteSpec[] = [
  { path: '/login', label: 'login', auth: false },
  { path: '/', label: 'home', auth: true },
  { path: '/instances', label: 'instances', auth: true },
  { path: '/instances/1', label: 'instances-1', auth: true },
  { path: '/firewall', label: 'firewall', auth: true },
  { path: '/routing', label: 'routing', auth: true },
  { path: '/firewall/simulator', label: 'firewall-simulator', auth: true },
  { path: '/firewall/tests', label: 'firewall-tests', auth: true },
  { path: '/firewall/nat', label: 'firewall-nat', auth: true },
  { path: '/traffic', label: 'traffic', auth: true },
  { path: '/vpn', label: 'vpn', auth: true },
  { path: '/dns', label: 'dns', auth: true },
  { path: '/dhcp', label: 'dhcp', auth: true },
  { path: '/vpn/create', label: 'vpn-create', auth: true },
  { path: '/vpn/servers/1', label: 'vpn-servers-1', auth: true },
  { path: '/mail', label: 'mail', auth: true },
  { path: '/mail/domains/create', label: 'mail-domains-create', auth: true },
  { path: '/mail/domains/1', label: 'mail-domains-1', auth: true },
  { path: '/users', label: 'users', auth: true },
  { path: '/metrics', label: 'metrics', auth: true },
  { path: '/audit', label: 'audit', auth: true },
  { path: '/settings', label: 'settings', auth: true },
  { path: '/admin/llm', label: 'admin-llm', auth: true },
]

function evidenceDir(): string {
  // Spec runs with cwd = web-ui; a git worktree reports the MAIN repo's
  // .git dir here, so evidence lands in the main checkout's .omo/.
  const gitDir = execSync('git rev-parse --path-format=absolute --git-common-dir')
    .toString()
    .trim()
  return path.join(path.resolve(gitDir, '..'), '.omo', 'evidence', 'frontend-redesign', 'a11y')
}

async function scanRoute(page: Page, route: RouteSpec, theme: 'light' | 'dark') {
  const results = await new AxeBuilder({ page }).analyze()
  const blocking = results.violations.filter(
    (v) => v.impact === 'serious' || v.impact === 'critical',
  )

  const dir = evidenceDir()
  await fs.promises.mkdir(dir, { recursive: true })
  await fs.promises.writeFile(
    path.join(dir, `${route.label}-${theme}.json`),
    JSON.stringify(
      {
        route: route.path,
        theme,
        scannedAt: new Date().toISOString(),
        summary: {
          violations: results.violations.length,
          passes: results.passes.length,
          incomplete: results.incomplete.length,
          inapplicable: results.inapplicable.length,
          seriousOrCritical: blocking.length,
        },
        violations: results.violations.map((v) => ({
          id: v.id,
          impact: v.impact,
          help: v.help,
          helpUrl: v.helpUrl,
          tags: v.tags,
          nodes: v.nodes.map((n) => ({
            target: n.target,
            html: n.html,
            failureSummary: n.failureSummary,
          })),
        })),
        incomplete: results.incomplete.map((v) => ({ id: v.id, impact: v.impact, help: v.help })),
      },
      null,
      2,
    ),
  )

  expect(
    blocking.map((v) => ({ id: v.id, impact: v.impact, nodes: v.nodes.length })),
    `${route.path} [${theme}] axe serious/critical violations`,
  ).toEqual([])
}

// Unset theme resolves to 'system'; pin the emulation so light is deterministic.
test.use({ colorScheme: 'light' })

for (const route of ROUTES) {
  test(`a11y ${route.label} (light+dark)`, async ({ page }) => {
    if (route.auth) {
      await seedAuthSession(page)
      await seedInstanceState(page)
      // Deterministic starting theme: the Header toggle cycles light→dark.
      await page.addInitScript(() => {
        window.localStorage.setItem('viswall-theme', 'light')
      })
    }

    await page.goto(route.path)
    await page.waitForLoadState('networkidle')
    if (route.auth) {
      await expect(page.locator('#main-content')).toBeVisible()
    }

    // LIGHT
    await expect(page.locator('html')).not.toHaveClass(/\bdark\b/)
    await scanRoute(page, route, 'light')

    // DARK — flip via the top-bar theme toggle on authenticated routes
    // (the login page has no header, so seed + re-navigate there).
    if (route.auth) {
      await page.getByRole('button', { name: 'Theme: light' }).click()
      // transition-colors interpolates for ~200ms after the flip — wait it
      // out or axe reads mid-transition color blends as violations
      await page.waitForTimeout(500)
    } else {
      await page.evaluate(() => window.localStorage.setItem('viswall-theme', 'dark'))
      await page.goto(route.path)
      await page.waitForLoadState('networkidle')
    }
    await expect(page.locator('html')).toHaveClass(/\bdark\b/)
    await scanRoute(page, route, 'dark')
  })
}
