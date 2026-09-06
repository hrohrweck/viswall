import { expect, test } from '@playwright/test'
import { seedAuthSession } from './helpers/auth'

/**
 * E2E spec for the ⌘K command palette.
 *
 * Tests keyboard shortcut (ControlOrMeta+K) and the top-bar trigger button.
 */
test.describe('command palette (MSW-seeded)', () => {
  test.beforeEach(async ({ page }) => {
    await seedAuthSession(page)
  })

  test('opens via ControlOrMeta+K, filters to VPN, Enter navigates to /vpn', async ({
    page,
  }) => {
    await page.goto('/')

    // Wait for the app shell to render.
    await expect(page.locator('header')).toBeVisible({ timeout: 15_000 })

    // Press the keyboard shortcut to open the palette.
    await page.keyboard.press('ControlOrMeta+k')

    // The palette input should be visible.
    const input = page.getByPlaceholder('Search pages, instances, actions…')
    await expect(input).toBeVisible()

    // Type 'vpn' to filter.
    await input.fill('vpn')

    // The VPN item should be visible.
    const vpnItem = page.locator('[cmdk-item]').filter({ hasText: 'VPN' }).first()
    await expect(vpnItem).toBeVisible()

    // Press Enter to navigate.
    await page.keyboard.press('Enter')

    // URL should be /vpn.
    await expect(page).toHaveURL(/\/vpn/)
  })

  test('opens via the top-bar search trigger button', async ({ page }) => {
    await page.goto('/')

    // Wait for the header.
    await expect(page.locator('header')).toBeVisible({ timeout: 15_000 })

    // Click the search trigger.
    await page.locator('[data-testid="command-palette-trigger"]').click()

    // The palette input should be visible.
    await expect(
      page.getByPlaceholder('Search pages, instances, actions…'),
    ).toBeVisible()
  })
})
