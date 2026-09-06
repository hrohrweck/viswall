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

    // The switcher button shows "Select instance" when nothing is selected.
    // Scope to the header to avoid matching dashboard content.
    const switcher = page.locator('header').getByRole('button', { name: /Select instance/i })
    await expect(switcher).toBeVisible({ timeout: 15_000 })

    // Open the instance switcher dropdown.
    await switcher.click()

    // Select edge-oslo-02 from the dropdown menu.
    await page.getByRole('menuitem', { name: /edge-oslo-02/i }).click()

    // The switcher button should now show edge-oslo-02 (scoped to header).
    await expect(
      page.locator('header').getByRole('button', { name: /edge-oslo-02/i }),
    ).toBeVisible()
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
