import { expect, test } from '@playwright/test'
import { expectNoSeriousA11yViolations } from './axe'
import { seedAuthSession } from './helpers/auth'

/**
 * Smoke spec for the MSW-seeded QA harness: a seeded session lands on the
 * dashboard, the three deterministic fixture instances render, and the page
 * has no serious/critical axe violations.
 *
 * Requires the dev server to run with MSW enabled:
 *   VITE_ENABLE_MSW=1 npm run dev
 */
test.describe('dashboard smoke (MSW-seeded)', () => {
  test.beforeEach(async ({ page }) => {
    await seedAuthSession(page)
  })

  test('shows seeded instances and passes axe serious check', async ({ page }) => {
    await page.goto('/')

    // Dashboard heading renders once the layout is up.
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible()

    // All three deterministic fixture instances are listed under System Status.
    // waitFor-style assertions absorb the async MSW worker startup + query retry.
    await expect(page.getByText('edge-berlin-01')).toBeVisible({ timeout: 15_000 })
    await expect(page.getByText('edge-oslo-02')).toBeVisible()
    await expect(page.getByText('edge-vie-03')).toBeVisible()

    await expectNoSeriousA11yViolations(page, 'dashboard')
  })
})
