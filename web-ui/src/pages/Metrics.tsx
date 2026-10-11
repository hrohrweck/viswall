import { useMemo, useState } from 'react'
import {
  Cpu,
  HardDrive,
  MemoryStick,
  Network,
  Mail,
  Activity,
  Info,
} from 'lucide-react'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts'
import { useInstanceStore } from '../stores/instance'
import {
  useMetricsLatest,
  useDashboardData,
  useMetricsQuery,
} from '../hooks/useApi'
import { Card, PageHeader, Skeleton, QueryError } from '../components/ui'
import { cn } from '../lib/utils'
import { CHART, chartTheme } from '../lib/chartColors'
import type { MetricSnapshot } from '../types'

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function formatBytes(bytes?: number): string {
  if (bytes === undefined || bytes === null) return '-'
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function formatPercent(value?: number): string {
  if (value === undefined || value === null) return '-'
  return value.toFixed(1) + '%'
}

/**
 * Backend timestamps are naive UTC (no offset suffix). Tag them as UTC so
 * labels show the user's local wall-clock time instead of a TZ-shifted one.
 */
function parseTimestamp(value: string): Date {
  return /[zZ]$|[+-]\d{2}:?\d{2}$/.test(value) ? new Date(value) : new Date(`${value}Z`)
}

function formatTimeLabel(value: string, withDays: boolean): string {
  return parseTimestamp(value).toLocaleString(
    [],
    withDays
      ? { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }
      : { hour: '2-digit', minute: '2-digit' },
  )
}

/* ------------------------------------------------------------------ */
/*  Static token-class map — replaces dynamically interpolated color names */
/* ------------------------------------------------------------------ */

const CARD_COLORS: Record<string, { bg: string; icon: string }> = {
  blue: { bg: 'bg-primary-subtle', icon: 'text-primary' },
  purple: { bg: 'bg-info-subtle', icon: 'text-info' },
  indigo: { bg: 'bg-info-subtle', icon: 'text-info' },
  orange: { bg: 'bg-warning-subtle', icon: 'text-warning' },
  green: { bg: 'bg-success-subtle', icon: 'text-success' },
}

/* ------------------------------------------------------------------ */
/*  Network interface histograms                                       */
/* ------------------------------------------------------------------ */

/** Upper bound for histogram buckets — keeps bars readable on 7d ranges. */
const IFACE_BUCKETS = 30

interface InterfaceSeries {
  name: string
  totals: { rx?: number; tx?: number }
  data: Array<{ label: string; rx: number; tx: number }>
}

/**
 * Builds per-interface traffic histograms from the collected snapshots.
 *
 * interface_stats holds cumulative byte counters, so the chart plots the
 * delta between consecutive snapshots (traffic during the interval),
 * clamped at 0 for counter resets. Deltas are bucketed so long ranges
 * stay readable.
 */
function buildInterfaceSeries(
  ascending: MetricSnapshot[],
  latest?: MetricSnapshot,
): InterfaceSeries[] {
  if (ascending.length === 0) return []

  // Interfaces in order of first appearance
  const names: string[] = []
  for (const s of ascending) {
    for (const iface of s.interface_stats ?? []) {
      if (!names.includes(iface.name)) names.push(iface.name)
    }
  }
  if (names.length === 0) return []

  const bucketSize = Math.max(1, Math.ceil(ascending.length / IFACE_BUCKETS))

  return names.map((name) => {
    let prev: { rx_bytes?: number; tx_bytes?: number } | undefined
    const deltas = ascending.map((s) => {
      const cur = s.interface_stats?.find((i) => i.name === name)
      const delta = {
        rx: cur && prev ? Math.max(0, (cur.rx_bytes ?? 0) - (prev.rx_bytes ?? 0)) : 0,
        tx: cur && prev ? Math.max(0, (cur.tx_bytes ?? 0) - (prev.tx_bytes ?? 0)) : 0,
      }
      prev = cur
      return delta
    })

    const data: InterfaceSeries['data'] = []
    for (let start = 0; start < ascending.length; start += bucketSize) {
      const end = Math.min(start + bucketSize, ascending.length)
      let rx = 0
      let tx = 0
      for (let i = start; i < end; i++) {
        rx += deltas[i].rx
        tx += deltas[i].tx
      }
      data.push({
        label: formatTimeLabel(ascending[start].timestamp, ascending.length > 24 * 2),
        rx,
        tx,
      })
    }

    const total = latest?.interface_stats?.find((i) => i.name === name)
    return { name, totals: { rx: total?.rx_bytes, tx: total?.tx_bytes }, data }
  })
}

/* ------------------------------------------------------------------ */
/*  Metrics page                                                       */
/* ------------------------------------------------------------------ */

export function Metrics() {
  const { selectedInstanceId } = useInstanceStore()
  const [timeRange, setTimeRange] = useState<'1h' | '24h' | '7d'>('24h')

  const { data: latest, isLoading: latestLoading } = useMetricsLatest(
    selectedInstanceId ?? 0,
  )
  const { data: dashboard, isLoading: dashboardLoading } = useDashboardData(
    selectedInstanceId ?? 0,
  )

  // Calculate time range for historical query.
  // Memoized so start_time/end_time are stable across renders — otherwise the
  // query key changes on every render and the query refetches endlessly.
  const { startTime, endTime } = useMemo(() => {
    const now = new Date()
    const startMap = {
      '1h': new Date(now.getTime() - 60 * 60 * 1000),
      '24h': new Date(now.getTime() - 24 * 60 * 60 * 1000),
      '7d': new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000),
    }
    return { startTime: startMap[timeRange], endTime: now }
  }, [timeRange])

  const {
    data: historical,
    isLoading: historicalLoading,
    isError: historicalError,
    refetch: refetchHistorical,
  } = useMetricsQuery(
    {
      instance_ids: selectedInstanceId ? [selectedInstanceId] : undefined,
      start_time: startTime.toISOString(),
      end_time: endTime.toISOString(),
      granularity: '5m',
    },
    { enabled: !!selectedInstanceId },
  )

  const chartThemeTokens = chartTheme()

  // Snapshots arrive newest-first; charts plot oldest-first.
  const ascending = useMemo(
    () => (historical ? [...historical].reverse() : []),
    [historical],
  )

  const withDays = timeRange === '7d'

  // Prepare chart data from historical snapshots
  const chartData = useMemo(
    () =>
      ascending.map((s) => ({
        time: formatTimeLabel(s.timestamp, withDays),
        cpu: s.cpu_percent ?? 0,
        memory: s.memory_percent ?? 0,
        disk: s.disk_percent ?? 0,
      })),
    [ascending, withDays],
  )

  const mailChartData = useMemo(
    () =>
      ascending.map((s) => ({
        time: formatTimeLabel(s.timestamp, withDays),
        inbound: s.mail_inbound_count ?? 0,
        outbound: s.mail_outbound_count ?? 0,
        spam: s.mail_spam_count ?? 0,
        virus: s.mail_virus_count ?? 0,
      })),
    [ascending, withDays],
  )

  const interfaceSeries = useMemo(
    () => buildInterfaceSeries(ascending, latest),
    [ascending, latest],
  )

  /* ── No instance selected ── */
  if (!selectedInstanceId) {
    return (
      <div>
        <PageHeader title="Metrics" />
        <Card className="mt-6">
          <div className="flex items-center gap-3 text-on-surface-muted">
            <Info className="h-5 w-5 shrink-0" />
            <p className="text-sm">
              Select an instance from the top bar to view its metrics.
            </p>
          </div>
        </Card>
      </div>
    )
  }

  const system = latest
  const counts = dashboard

  // Only deployed functions get metric sections on a host — mail
  // telemetry does not exist for hosts without mail domains.
  const mailDeployed = (counts?.mail_domain_count ?? 0) > 0

  const statCards = [
    {
      label: 'CPU Usage',
      value: formatPercent(system?.cpu_percent),
      icon: Cpu,
      color: 'blue',
      detail: 'Current',
    },
    {
      label: 'Memory Usage',
      value: formatPercent(system?.memory_percent),
      icon: MemoryStick,
      color: 'purple',
      detail: system?.memory_used_bytes
        ? `${formatBytes(system.memory_used_bytes)} / ${formatBytes(system.memory_total_bytes)}`
        : 'Current',
    },
    {
      label: 'Disk Usage',
      value: formatPercent(system?.disk_percent),
      icon: HardDrive,
      color: 'orange',
      detail: system?.disk_used_bytes
        ? `${formatBytes(system.disk_used_bytes)} / ${formatBytes(system.disk_total_bytes)}`
        : 'Current',
    },
    ...(mailDeployed
      ? [
          {
            label: 'Mail Queue',
            value: system?.mail_queue_size?.toString() ?? '-',
            icon: Mail,
            color: 'green',
            detail: 'Messages',
          },
        ]
      : []),
  ]

  /* ── Segmented time-range control ── */
  const timeRangeControl = (
    <div className="inline-flex rounded-lg border border-border" role="group">
      {(['1h', '24h', '7d'] as const).map((range) => (
        <button
          key={range}
          onClick={() => setTimeRange(range)}
          className={cn(
            'px-3 py-1.5 text-sm font-medium transition-colors first:rounded-l-lg last:rounded-r-lg',
            timeRange === range
              ? 'bg-primary-subtle text-primary'
              : 'text-on-surface-muted hover:bg-surface-elevated',
          )}
        >
          {range}
        </button>
      ))}
    </div>
  )

  return (
    <div>
      <PageHeader
        title="Metrics"
        description="Host resource usage and metrics of the functions deployed on this instance"
        secondaryActions={[timeRangeControl]}
      />

      {/* ── Count Cards (deployed functions only) ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6 mb-6">
        {dashboardLoading ? (
          <>
            <Skeleton className="h-20" />
            <Skeleton className="h-20" />
            <Skeleton className="h-20" />
          </>
        ) : (
          (
            [
              {
                count: counts?.firewall_rule_count ?? 0,
                label: 'Firewall Rules',
                icon: Activity,
                color: 'blue',
              },
              {
                count: counts?.mail_domain_count ?? 0,
                label: 'Mail Domains',
                icon: Mail,
                color: 'purple',
              },
              {
                count: counts?.vpn_server_count ?? 0,
                label: 'VPN Servers',
                icon: Network,
                color: 'indigo',
              },
            ] as const
          )
            .filter(({ count }) => count > 0)
            .map(({ count, label, icon: Icon, color }) => (
              <Card key={label}>
                <div className="flex items-center gap-3">
                  <div className={cn('p-2 rounded-lg', CARD_COLORS[color].bg)}>
                    <Icon className={cn('w-5 h-5', CARD_COLORS[color].icon)} />
                  </div>
                  <div>
                    <p className="text-sm text-on-surface-muted">{label}</p>
                    <p className="text-2xl font-bold text-on-surface">{count}</p>
                  </div>
                </div>
              </Card>
            ))
        )}
      </div>

      {/* ── System Stats ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {latestLoading ? (
          <>
            <Skeleton className="h-24" />
            <Skeleton className="h-24" />
            <Skeleton className="h-24" />
            <Skeleton className="h-24" />
          </>
        ) : (
          statCards.map(({ label, value, icon: Icon, color, detail }) => (
            <Card key={label}>
              <div className="flex items-center gap-3">
                <div className={cn('p-2 rounded-lg', CARD_COLORS[color].bg)}>
                  <Icon className={cn('w-5 h-5', CARD_COLORS[color].icon)} />
                </div>
                <div>
                  <p className="text-sm text-on-surface-muted">{label}</p>
                  <p className="text-2xl font-bold text-on-surface">{value}</p>
                  <p className="text-xs text-on-surface-muted">{detail}</p>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>

      {/* ── Charts ── */}
      <div
        className={cn(
          'grid gap-6 mb-6',
          mailDeployed ? 'grid-cols-1 lg:grid-cols-2' : 'grid-cols-1',
        )}
      >
        <Card title="System Resources">
          {historicalLoading ? (
            <Skeleton className="h-[250px] w-full" />
          ) : historicalError ? (
            <QueryError onRetry={() => void refetchHistorical()} />
          ) : chartData.length === 0 ? (
            <p className="text-sm text-on-surface-muted text-center py-12">
              No metrics in range
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke={chartThemeTokens.grid} />
                <XAxis dataKey="time" tick={{ fill: chartThemeTokens.axis }} />
                <YAxis unit="%" tick={{ fill: chartThemeTokens.axis }} />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="cpu"
                  stroke={CHART.primary}
                  fill={CHART.primary}
                  fillOpacity={0.1}
                  name="CPU %"
                />
                <Area
                  type="monotone"
                  dataKey="memory"
                  stroke={CHART.secondary}
                  fill={CHART.secondary}
                  fillOpacity={0.1}
                  name="Memory %"
                />
                <Area
                  type="monotone"
                  dataKey="disk"
                  stroke={CHART.tertiary}
                  fill={CHART.tertiary}
                  fillOpacity={0.1}
                  name="Disk %"
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </Card>

        {mailDeployed && (
          <Card title="Mail Activity">
            {historicalLoading ? (
              <Skeleton className="h-[250px] w-full" />
            ) : historicalError ? (
              <QueryError onRetry={() => void refetchHistorical()} />
            ) : mailChartData.length === 0 ? (
              <p className="text-sm text-on-surface-muted text-center py-12">
                No metrics in range
              </p>
            ) : (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={mailChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={chartThemeTokens.grid} />
                  <XAxis dataKey="time" tick={{ fill: chartThemeTokens.axis }} />
                  <YAxis tick={{ fill: chartThemeTokens.axis }} />
                  <Tooltip />
                  <Bar dataKey="inbound" fill={CHART.primary} name="Inbound" />
                  <Bar dataKey="outbound" fill={CHART.secondary} name="Outbound" />
                  <Bar dataKey="spam" fill={CHART.danger} name="Spam" />
                  <Bar dataKey="virus" fill={CHART.tertiary} name="Virus" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </Card>
        )}
      </div>

      {/* ── Network Interfaces ── */}
      {historicalLoading ? null : interfaceSeries.length > 0 ? (
        <Card title="Network Interfaces" padding="" className="mb-6">
          <div className="divide-y divide-border">
            {interfaceSeries.map((series) => {
              const hasTraffic = series.data.some((d) => d.rx > 0 || d.tx > 0)
              return (
                <div key={series.name} className="px-5 py-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <Network className="w-4 h-4 text-on-surface-muted" />
                      <span className="font-medium text-on-surface">
                        {series.name}
                      </span>
                    </div>
                    <div className="flex items-center gap-5 text-sm text-on-surface-muted">
                      <span className="flex items-center gap-1.5">
                        <span
                          className="inline-block w-2.5 h-2.5 rounded-sm"
                          style={{ background: CHART.success }}
                        />
                        RX {formatBytes(series.totals.rx)}
                      </span>
                      <span className="flex items-center gap-1.5">
                        <span
                          className="inline-block w-2.5 h-2.5 rounded-sm"
                          style={{ background: CHART.primary }}
                        />
                        TX {formatBytes(series.totals.tx)}
                      </span>
                    </div>
                  </div>
                  {hasTraffic ? (
                    <ResponsiveContainer width="100%" height={160}>
                      <BarChart data={series.data}>
                        <CartesianGrid
                          strokeDasharray="3 3"
                          stroke={chartThemeTokens.grid}
                          vertical={false}
                        />
                        <XAxis
                          dataKey="label"
                          tick={{ fill: chartThemeTokens.axis, fontSize: 11 }}
                          interval="preserveStartEnd"
                        />
                        <YAxis
                          tickFormatter={(v) => formatBytes(Number(v))}
                          tick={{ fill: chartThemeTokens.axis, fontSize: 11 }}
                          width={72}
                        />
                        <Tooltip formatter={(v) => formatBytes(Number(v))} />
                        <Bar dataKey="rx" fill={CHART.success} name="RX" />
                        <Bar dataKey="tx" fill={CHART.primary} name="TX" />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <p className="text-sm text-on-surface-muted text-center py-8">
                      No traffic recorded in this range yet — snapshots are
                      collected every minute
                    </p>
                  )}
                </div>
              )
            })}
          </div>
        </Card>
      ) : null}
    </div>
  )
}
