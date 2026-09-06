/**
 * Shared chart colour constants for Recharts.
 *
 * Recharts needs literal hex strings — Tailwind utility classes cannot be
 * interpolated into SVG `stroke`/`fill` props.  Every colour used in charts
 * lives here so dark-mode and light-mode palettes stay in one place.
 */

export const CHART = {
  /** CPU — primary indigo */
  primary: '#4f46e5',
  /** Memory — teal */
  secondary: '#0f766e',
  /** Disk — amber */
  tertiary: '#b45309',
  /** Positive deltas / healthy indicators */
  success: '#059669',
  /** Negative deltas / danger indicators */
  danger: '#e11d48',
  /** Grid lines — light mode */
  grid: '#e2e8f0',
  /** Grid lines — dark mode */
  gridDark: '#243049',
  /** Axis tick labels — light mode */
  axis: '#64748b',
  /** Axis tick labels — dark mode */
  axisDark: '#94a3b8',
} as const

export interface ChartThemeTokens {
  grid: string
  axis: string
}

/**
 * Returns grid / axis colours that match the current theme.
 *
 * Reads `document.documentElement.classList` so callers don't need to wire
 * React context — safe for non-React helpers and Recharts customisation
 * callbacks.
 */
export function chartTheme(isDark?: boolean): ChartThemeTokens {
  const dark =
    isDark ?? (typeof document !== 'undefined' && document.documentElement.classList.contains('dark'))
  return {
    grid: dark ? CHART.gridDark : CHART.grid,
    axis: dark ? CHART.axisDark : CHART.axis,
  }
}
