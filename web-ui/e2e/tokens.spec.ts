import { expect, test } from '@playwright/test';

// Token parity spec — executed by the todo 4 Playwright harness (this file is
// committed in todo 2; do not run before playwright.config.ts exists).
// Asserts semantic tokens resolve to the right computed values in both themes
// and that the `<alpha-value>` wiring keeps opacity modifiers working.

const RGB = (r: number, g: number, b: number, a = 1) =>
  `rgba(${r}, ${g}, ${b}, ${a})`;

const LIGHT = {
  surface: RGB(248, 250, 252),
  onSurface: RGB(15, 23, 42),
  border: RGB(226, 232, 240),
  radius: '8px',
  mono: '"JetBrains Mono"',
};

const DARK = {
  surface: RGB(11, 18, 32),
  onSurface: RGB(226, 232, 240),
  border: RGB(36, 48, 73),
  radius: '8px',
  mono: '"JetBrains Mono"',
};

test.beforeEach(async ({ page }) => {
  await page.goto('/');
  await page.evaluate(() => {
    document.documentElement.classList.remove('dark');
    const probe = document.createElement('div');
    probe.id = 'token-probe';
    probe.className =
      'bg-surface text-on-surface border-border rounded-card font-mono';
    document.body.appendChild(probe);
    const alphaProbe = document.createElement('div');
    alphaProbe.id = 'alpha-probe';
    alphaProbe.className = 'bg-primary/50';
    document.body.appendChild(alphaProbe);
  });
});

test('semantic tokens resolve to light theme values', async ({ page }) => {
  const probe = page.locator('#token-probe');
  await expect(probe).toHaveCSS('background-color', LIGHT.surface);
  await expect(probe).toHaveCSS('color', LIGHT.onSurface);
  await expect(probe).toHaveCSS('border-color', LIGHT.border);
  await expect(probe).toHaveCSS('border-radius', LIGHT.radius);
  await expect(probe).toHaveCSS('font-family', new RegExp(LIGHT.mono));
});

test('semantic tokens flip to dark theme under .dark', async ({ page }) => {
  await page.evaluate(() => document.documentElement.classList.add('dark'));
  const probe = page.locator('#token-probe');
  await expect(probe).toHaveCSS('background-color', DARK.surface);
  await expect(probe).toHaveCSS('color', DARK.onSurface);
  await expect(probe).toHaveCSS('border-color', DARK.border);
  await expect(probe).toHaveCSS('border-radius', DARK.radius);
  await expect(probe).toHaveCSS('font-family', new RegExp(DARK.mono));
});

test('bg-primary/50 renders at ~50% alpha', async ({ page }) => {
  const bg = await page
    .locator('#alpha-probe')
    .evaluate((el) => getComputedStyle(el).backgroundColor);
  const match = bg.match(/rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)/);
  expect(match).not.toBeNull();
  const alpha = Number(match![4]);
  expect(alpha).toBeGreaterThan(0.45);
  expect(alpha).toBeLessThan(0.55);
});
