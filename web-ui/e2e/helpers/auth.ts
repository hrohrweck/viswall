import { expect, type Page } from '@playwright/test'
import { loginResponse, validCredentials } from '../../src/test/msw/fixtures'

/**
 * Sign-in helpers for the MSW-seeded e2e harness.
 *
 * `seedAuthSession` (preferred, fast) writes the zustand-persist payload that
 * src/stores/auth.ts expects — localStorage key 'viswall-auth' with shape
 * { state: { token, user }, version: 0 } — before any app code runs.
 *
 * `loginViaUi` (fallback) drives the real Login page; the MSW browser worker
 * answers POST /api/v1/auth/login with the canned fixture response.
 */
export async function seedAuthSession(page: Page): Promise<void> {
  await page.addInitScript((payload) => {
    window.localStorage.setItem(
      'viswall-auth',
      JSON.stringify({
        state: { token: payload.access_token, user: payload.user },
        version: 0,
      }),
    )
  }, loginResponse)
}

/**
 * Seeds the persisted instance store (src/stores/instance.ts) so
 * instance-scoped pages render their per-instance data instead of the
 * EmptyState + InstanceSelector fallback. Defaults to fixture instance 1
 * (edge-berlin-01, active).
 */
export async function seedInstanceState(page: Page, instanceId = 1): Promise<void> {
  await page.addInitScript((id) => {
    window.localStorage.setItem(
      'viswall-instance',
      JSON.stringify({ state: { selectedInstanceId: id }, version: 0 }),
    )
  }, instanceId)
}

export async function loginViaUi(page: Page): Promise<void> {
  await page.goto('/login')
  // The Login page labels are not programmatically associated with their
  // inputs (pre-existing markup), so the fields are selected by type —
  // same strategy as src/test/msw-smoke.test.tsx.
  await page.locator('input[type="text"]').fill(validCredentials.username)
  await page.locator('input[type="password"]').fill(validCredentials.password)
  await page.getByRole('button', { name: 'Sign In' }).click()
  await expect(page).toHaveURL('/')
}
