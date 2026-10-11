import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { http, HttpResponse } from 'msw'
import { server } from './msw/node'
import { dashboardData, metricsHistory } from './msw/fixtures'
import { useInstanceStore } from '../stores/instance'
import { Metrics } from '../pages/Metrics'
import { chartTheme } from '../lib/chartColors'

/**
 * Metrics page tests — Task 25.
 *
 * Covers: instance-notice, segmented time-range control, stat card static
 * classes, chartTheme helper (light/dark), and error state QueryError.
 */

// jsdom has no ResizeObserver; recharts ResponsiveContainer requires it once
// the metrics query settles and charts mount. The stub reports a fixed size
// on observe so ResponsiveContainer actually renders its chart children.
vi.stubGlobal(
  'ResizeObserver',
  class {
    private cb: ResizeObserverCallback
    constructor(cb: ResizeObserverCallback) {
      this.cb = cb
    }
    observe(target: Element) {
      this.cb(
        [
          {
            target,
            contentRect: { width: 800, height: 250 },
          } as unknown as ResizeObserverEntry,
        ],
        this as unknown as ResizeObserver,
      )
    }
    unobserve() {}
    disconnect() {}
  },
)

function createWrapper() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={qc}>
        <MemoryRouter>{children}</MemoryRouter>
      </QueryClientProvider>
    )
  }
}

beforeEach(() => {
  useInstanceStore.setState({ selectedInstanceId: 1 })
})

describe('Metrics', () => {
  it('instance-notice renders when no instance selected', () => {
    useInstanceStore.setState({ selectedInstanceId: null })

    const Wrapper = createWrapper()
    render(<Metrics />, { wrapper: Wrapper })

    expect(
      screen.getByText(/Select an instance from the top bar to view its metrics/i),
    ).toBeInTheDocument()
  })

  it('segmented time-range control toggles active class', async () => {
    const Wrapper = createWrapper()
    render(<Metrics />, { wrapper: Wrapper })

    const btn1h = screen.getByRole('button', { name: '1h' })
    const btn24h = screen.getByRole('button', { name: '24h' })
    const btn7d = screen.getByRole('button', { name: '7d' })

    // 24h is the default active range
    expect(btn24h.className).toContain('bg-primary-subtle')
    expect(btn24h.className).toContain('text-primary')
    expect(btn1h.className).not.toContain('bg-primary-subtle')

    // Switch to 1h
    await userEvent.click(btn1h)
    expect(btn1h.className).toContain('bg-primary-subtle')
    expect(btn1h.className).toContain('text-primary')
    expect(btn24h.className).not.toContain('bg-primary-subtle')

    // Switch to 7d
    await userEvent.click(btn7d)
    expect(btn7d.className).toContain('bg-primary-subtle')
    expect(btn7d.className).toContain('text-primary')
    expect(btn1h.className).not.toContain('bg-primary-subtle')
  })

  it('stat cards use static token classes from CARD_COLORS map', async () => {
    const Wrapper = createWrapper()
    render(<Metrics />, { wrapper: Wrapper })

    // Wait for stat cards to render
    await screen.findByText('CPU Usage')

    // Find the icon container for CPU (blue) — it's a div.rounded-lg inside the card
    const cpuLabel = screen.getByText('CPU Usage')
    const cpuCard = cpuLabel.closest('[class*="rounded-card"]')
    // The icon container is the first .rounded-lg descendant
    const iconContainer = cpuCard?.querySelector('.rounded-lg')

    expect(iconContainer).toBeTruthy()
    // Assert the literal static token class, not a template interpolation
    expect(iconContainer!.className).toContain('bg-primary-subtle')
    expect(iconContainer!.querySelector('svg')?.getAttribute('class')).toContain('text-primary')
  })

  it('error state renders QueryError when query errors', async () => {
    // Override the metrics/query handler to return a 500
    server.use(
      http.post('/api/v1/metrics/query', () =>
        HttpResponse.json({ detail: 'Internal error' }, { status: 500 }),
      ),
    )

    const Wrapper = createWrapper()
    render(<Metrics />, { wrapper: Wrapper })

    // Wait for the QueryError to render
    await screen.findAllByText('Something went wrong')

    expect(screen.getAllByText('Something went wrong')).toHaveLength(2)
    expect(screen.getAllByRole('button', { name: /retry/i })).toHaveLength(2)
  })

  it('renders per-interface traffic histograms from historical snapshots', async () => {
    // The API returns snapshots newest-first; the page plots oldest-first
    server.use(
      http.post('/api/v1/metrics/query', () =>
        HttpResponse.json([...metricsHistory].reverse()),
      ),
    )

    const Wrapper = createWrapper()
    render(<Metrics />, { wrapper: Wrapper })

    // Both interfaces from the snapshots are listed with their totals
    expect(await screen.findByText('wan0')).toBeInTheDocument()
    expect(screen.getByText('lan0')).toBeInTheDocument()

    // One traffic histogram (Recharts wrapper) per interface
    await screen.findByText('Network Interfaces')
    const charts = document.querySelectorAll('.recharts-wrapper')
    expect(charts.length).toBeGreaterThanOrEqual(2)
  })

  it('shows the collecting hint for interfaces without traffic deltas', async () => {
    // Default handler returns a single snapshot — no counter deltas yet
    const Wrapper = createWrapper()
    render(<Metrics />, { wrapper: Wrapper })

    expect(await screen.findByText('wan0')).toBeInTheDocument()
    expect(
      screen.getAllByText(/No traffic recorded in this range yet/i).length,
    ).toBeGreaterThanOrEqual(1)
  })

  it('hides mail sections when mail is not deployed on the instance', async () => {
    // Override the dashboard handler: no mail domains on this host
    server.use(
      http.get('/api/v1/metrics/dashboard/1', () =>
        HttpResponse.json({
          ...dashboardData,
          mail_domain_count: 0,
        }),
      ),
    )

    const Wrapper = createWrapper()
    render(<Metrics />, { wrapper: Wrapper })

    await screen.findByText('CPU Usage')

    // Mail-only metric sections are gone…
    expect(screen.queryByText('Mail Queue')).not.toBeInTheDocument()
    expect(screen.queryByText('Mail Activity')).not.toBeInTheDocument()
    // …and the zero-count function card is not shown either
    expect(screen.queryByText('Mail Domains')).not.toBeInTheDocument()
    // Deployed functions still show
    expect(screen.getByText('Firewall Rules')).toBeInTheDocument()
    expect(screen.getByText('System Resources')).toBeInTheDocument()
  })
})

describe('chartTheme', () => {
  it('returns light grid/axis values by default', () => {
    // Ensure no .dark class on <html>
    document.documentElement.classList.remove('dark')
    const theme = chartTheme()
    expect(theme.grid).toBe('#e2e8f0')
    expect(theme.axis).toBe('#64748b')
  })

  it('returns dark grid/axis values when isDark is true', () => {
    const theme = chartTheme(true)
    expect(theme.grid).toBe('#243049')
    expect(theme.axis).toBe('#94a3b8')
  })

  it('reads .dark class from documentElement when isDark omitted', () => {
    document.documentElement.classList.add('dark')
    const theme = chartTheme()
    expect(theme.grid).toBe('#243049')
    expect(theme.axis).toBe('#94a3b8')

    // Cleanup
    document.documentElement.classList.remove('dark')
    const light = chartTheme()
    expect(light.grid).toBe('#e2e8f0')
    expect(light.axis).toBe('#64748b')
  })
})
