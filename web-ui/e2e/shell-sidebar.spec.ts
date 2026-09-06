import { expect, test } from '@playwright/test'
import { seedAuthSession } from './helpers/auth'

/**
 * Sidebar grouped navigation and collapse rail e2e spec.
 *
 * Requires the dev server to run with MSW enabled:
 *   VITE_ENABLE_MSW=1 npm run dev -- --host ::1
 */
test.describe('sidebar grouped navigation', () => {
  test.beforeEach(async ({ page }) => {
    await seedAuthSession(page)
    await page.goto('/')
    await page.waitForLoadState('networkidle')
  })

  test('renders all group labels', async ({ page }) => {
    const sidebar = page.locator('aside nav')
    for (const label of ['Overview', 'Network', 'Services', 'Administration']) {
      await expect(sidebar.getByText(label, { exact: true })).toBeVisible()
    }
  })

  test('collapse toggle switches to rail mode — labels hidden', async ({ page }) => {
    // Sidebar starts expanded
    const sidebar = page.locator('aside')
    await expect(sidebar.getByText('Dashboard')).toBeVisible()

    // Click collapse toggle
    const toggle = sidebar.getByRole('button', { name: 'Collapse sidebar' })
    await toggle.click()

    // Labels should be hidden in rail mode
    await expect(sidebar.getByText('Dashboard')).not.toBeVisible()
    await expect(sidebar.getByText('Overview', { exact: true })).not.toBeVisible()

    // Toggle shows "Expand"
    await expect(sidebar.getByRole('button', { name: 'Expand sidebar' })).toBeVisible()
  })
})
