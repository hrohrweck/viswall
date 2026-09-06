import { expect, test } from '@playwright/test'
import { seedAuthSession } from './helpers/auth'

/**
 * E2E spec for the responsive sidebar drawer.
 *
 * Tests mobile (390x844) and desktop (1440x900) viewports.
 */
test.describe('responsive sidebar drawer', () => {
  test.beforeEach(async ({ page }) => {
    await seedAuthSession(page)
  })

  test('mobile viewport: hamburger visible, drawer opens/closes via hamburger and scrim', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Hamburger is visible on mobile.
    const hamburger = page.getByRole('button', { name: 'Open navigation' })
    await expect(hamburger).toBeVisible({ timeout: 15_000 })

    // Drawer wrapper starts with translate-x-[-100%] (off-screen).
    const drawer = page.locator('.fixed.inset-y-0')
    await expect(drawer).toHaveClass(/translate-x-\[-100%\]/)

    // Click hamburger to open drawer.
    await hamburger.click()

    // Drawer slides in — wrapper now has translate-x-0.
    await expect(drawer).toHaveClass(/translate-x-0/)

    // Scrim is present.
    const scrim = page.locator('[data-testid="sidebar-scrim"]')
    await expect(scrim).toBeVisible()

    // Sidebar labels are now visible inside the open drawer.
    await expect(page.locator('aside').getByText('Dashboard')).toBeVisible()

    // Click scrim to close (click on the right side, away from the drawer).
    await scrim.click({ position: { x: 350, y: 400 } })

    // Drawer closes — wrapper back to translate-x-[-100%].
    await expect(drawer).toHaveClass(/translate-x-\[-100%\]/)
  })

  test('desktop viewport: hamburger hidden, sidebar docked visible', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Hamburger has lg:hidden class (CSS hides it on desktop).
    const hamburger = page.locator('header button[aria-label="Open navigation"]')
    await expect(hamburger).toHaveClass(/lg:hidden/)

    // Sidebar should be docked and visible.
    await expect(page.locator('aside').getByText('Dashboard')).toBeVisible()
  })

  test('body overflow is hidden while drawer is open', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Open the drawer.
    await page.getByRole('button', { name: 'Open navigation' }).click()

    // Wait for drawer to be open.
    const drawer = page.locator('.fixed.inset-y-0')
    await expect(drawer).toHaveClass(/translate-x-0/)

    // Assert body overflow is hidden.
    const overflow = await page.evaluate(() => document.body.style.overflow)
    expect(overflow).toBe('hidden')

    // Close via scrim (click right side, away from drawer at z-50).
    await page.locator('[data-testid="sidebar-scrim"]').click({ position: { x: 350, y: 400 } })

    // Body overflow should be restored.
    await page.waitForFunction(() => document.body.style.overflow === '', null, {
      timeout: 3000,
    })
  })
})
