import { expect, test } from '@playwright/test'
import { seedAuthSession } from './helpers/auth'

/**
 * E2E spec for the shell topbar: instance switching and theme toggle.
 *
 * Requires the dev server to run with MSW enabled:
 *   VITE_ENABLE_MSW=1 npm run dev -- --host ::1
 */
test.describe('shell topbar (MSW-seeded)', () => {
  test.beforeEach(async ({ page }) => {
    await seedAuthSession(page)
  })

  test('switches instance in the top bar and updates selected name', async ({ page }) => {
    await page.goto('/')

    // Wait for the instance switcher to show the first instance.
    await expect(page.getByText('edge-berlin-01')).toBeVisible({ timeout: 15_000 })

    // Open the instance switcher dropdown.
    await page.getByText('edge-berlin-01').first().click()

    // Select edge-oslo-02.
    await page.getByText('edge-oslo-02').click()

    // The switcher should now display edge-oslo-02 as the selected instance.
    // There may be multiple occurrences (trigger + sidebar), so use first().
    await expect(page.getByText('edge-oslo-02').first()).toBeVisible()
  })

  test('theme toggle flips html.dark', async ({ page }) => {
    await page.goto('/')

    // Wait for the header to be present.
    await expect(page.locator('[aria-label^="Theme"]')).toBeVisible({ timeout: 15_000 })

    // Click theme toggle: system → light.
    await page.locator('[aria-label^="Theme"]').click()

    // Click again: light → dark.
    await page.locator('[aria-label^="Theme"]').click()

    // html should now have the 'dark' class.
    await expect(page.locator('html')).toHaveClass(/dark/)
  })
})
