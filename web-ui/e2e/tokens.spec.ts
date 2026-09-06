import { expect, test } from '@playwright/test';

// Token parity spec — executed by the todo 4 Playwright harness.
// Asserts semantic tokens resolve to the right computed values in both themes
// and that the `<alpha-value>` wiring keeps opacity modifiers working.

// Chromium serializes OPAQUE colors as `rgb(r,g,b)` (no alpha component) and
// non-opaque as `rgba(r,g,b,a)` — parse both into a numeric tuple so theme
// assertions are format-tolerant but value-exact.
function parseColor(color: string): [number, number, number, number] {
  const match = color.match(/rgba?\(\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)(?:[,\s/]+([\d.]+))?\s*\)/);
  expect(match, `unparseable computed color: ${color}`).not.toBeNull();
  return [
    Number(match![1]),
    Number(match![2]),
    Number(match![3]),
    match![4] === undefined ? 1 : Number(match![4]),
  ];
}

const RGB = (r: number, g: number, b: number): [number, number, number, number] => [r, g, b, 1];

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

async function expectCssColor(
  page: import('@playwright/test').Page,
  selector: string,
  property: 'background-color' | 'color' | 'border-color',
  expected: [number, number, number, number],
) {
  const raw = await page
    .locator(selector)
    .evaluate((el, prop) => getComputedStyle(el)[prop as 'color'], property);
  expect(parseColor(raw)).toEqual(expected);
}

test.beforeEach(async ({ page }) => {
  // `/` redirects to `/login` client-side; going straight there (and waiting
  // past vite's first-visit dep re-optimization reload) keeps the execution
  // context stable for the probe injection below.
  await page.goto('/login');
  await page.waitForLoadState('networkidle');
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
  await expectCssColor(page, '#token-probe', 'background-color', LIGHT.surface);
  await expectCssColor(page, '#token-probe', 'color', LIGHT.onSurface);
  await expectCssColor(page, '#token-probe', 'border-color', LIGHT.border);
  await expect(probe).toHaveCSS('border-radius', LIGHT.radius);
  await expect(probe).toHaveCSS('font-family', new RegExp(LIGHT.mono));
});

test('semantic tokens flip to dark theme under .dark', async ({ page }) => {
  await page.evaluate(() => document.documentElement.classList.add('dark'));
  const probe = page.locator('#token-probe');
  await expectCssColor(page, '#token-probe', 'background-color', DARK.surface);
  await expectCssColor(page, '#token-probe', 'color', DARK.onSurface);
  await expectCssColor(page, '#token-probe', 'border-color', DARK.border);
  await expect(probe).toHaveCSS('border-radius', DARK.radius);
  await expect(probe).toHaveCSS('font-family', new RegExp(DARK.mono));
});

test('bg-primary/50 renders at ~50% alpha', async ({ page }) => {
  const bg = await page
    .locator('#alpha-probe')
    .evaluate((el) => getComputedStyle(el).backgroundColor);
  const [, , , alpha] = parseColor(bg);
  expect(alpha).toBeGreaterThan(0.45);
  expect(alpha).toBeLessThan(0.55);
});
