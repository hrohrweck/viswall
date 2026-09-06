import { useMemo, useState } from 'react'
import {
  Cpu,
  HardDrive,
  MemoryStick,
  Network,
  Mail,
  Activity,
  ArrowUpDown,
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

/* ------------------------------------------------------------------ */
/*  Static token-class map — replaces dynamic `bg-${color}` templates  */
/* ------------------------------------------------------------------ */

const CARD_COLORS: Record<string, { bg: string; icon: string }> = {
  blue: { bg: 'bg-blue-100 dark:bg-gray-800', icon: 'text-blue-600 dark:text-gray-300' },
  purple: { bg: 'bg-purple-100 dark:bg-gray-800', icon: 'text-purple-600 dark:text-gray-300' },
  indigo: { bg: 'bg-indigo-100 dark:bg-gray-800', icon: 'text-indigo-600 dark:text-gray-300' },
  orange: { bg: 'bg-orange-100 dark:bg-gray-800', icon: 'text-orange-600 dark:text-gray-300' },
  green: { bg: 'bg-green-100 dark:bg-gray-800', icon: 'text-green-600 dark:text-gray-300' },
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

  // Prepare chart data from historical snapshots
  const chartData =
    historical
      ?.slice()
      .reverse()
      .map((s) => ({
        time: new Date(s.timestamp).toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
        }),
        cpu: s.cpu_percent ?? 0,
        memory: s.memory_percent ?? 0,
        disk: s.disk_percent ?? 0,
      })) ?? []

  const mailChartData =
    historical
      ?.slice()
      .reverse()
      .map((s) => ({
        time: new Date(s.timestamp).toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
        }),
        inbound: s.mail_inbound_count ?? 0,
        outbound: s.mail_outbound_count ?? 0,
        spam: s.mail_spam_count ?? 0,
        virus: s.mail_virus_count ?? 0,
      })) ?? []

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
    {
      label: 'Mail Queue',
      value: system?.mail_queue_size?.toString() ?? '-',
      icon: Mail,
      color: 'green',
      detail: 'Messages',
    },
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
        description="System resource usage and mail activity"
        secondaryActions={[timeRangeControl]}
      />

      {/* ── Count Cards ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6 mb-6">
        {dashboardLoading ? (
          <>
            <Skeleton className="h-20" />
            <Skeleton className="h-20" />
            <Skeleton className="h-20" />
          </>
        ) : (
          <>
            <Card>
              <div className="flex items-center gap-3">
                <div className={cn('p-2 rounded-lg', CARD_COLORS.blue.bg)}>
                  <Activity className={cn('w-5 h-5', CARD_COLORS.blue.icon)} />
                </div>
                <div>
                  <p className="text-sm text-on-surface-muted">Firewall Rules</p>
                  <p className="text-2xl font-bold text-on-surface">
                    {counts?.firewall_rule_count ?? 0}
                  </p>
                </div>
              </div>
            </Card>
            <Card>
              <div className="flex items-center gap-3">
                <div className={cn('p-2 rounded-lg', CARD_COLORS.purple.bg)}>
                  <Mail className={cn('w-5 h-5', CARD_COLORS.purple.icon)} />
                </div>
                <div>
                  <p className="text-sm text-on-surface-muted">Mail Domains</p>
                  <p className="text-2xl font-bold text-on-surface">
                    {counts?.mail_domain_count ?? 0}
                  </p>
                </div>
              </div>
            </Card>
            <Card>
              <div className="flex items-center gap-3">
                <div className={cn('p-2 rounded-lg', CARD_COLORS.indigo.bg)}>
                  <Network className={cn('w-5 h-5', CARD_COLORS.indigo.icon)} />
                </div>
                <div>
                  <p className="text-sm text-on-surface-muted">VPN Servers</p>
                  <p className="text-2xl font-bold text-on-surface">
                    {counts?.vpn_server_count ?? 0}
                  </p>
                </div>
              </div>
            </Card>
          </>
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
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
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
      </div>

      {/* ── Network Interfaces ── */}
      {system?.interface_stats && system.interface_stats.length > 0 && (
        <Card title="Network Interfaces" padding="" className="mb-6">
          <div className="divide-y divide-border">
            {system.interface_stats.map((iface) => (
              <div
                key={iface.name}
                className="px-5 py-4 flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <Network className="w-5 h-5 text-on-surface-muted" />
                  <span className="font-medium text-on-surface">
                    {iface.name}
                  </span>
                </div>
                <div className="flex items-center gap-6 text-sm text-on-surface-muted">
                  <div className="flex items-center gap-1">
                    <ArrowUpDown className="w-4 h-4 text-success" />
                    <span>RX: {formatBytes(iface.rx_bytes)}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <ArrowUpDown className="w-4 h-4 text-primary" />
                    <span>TX: {formatBytes(iface.tx_bytes)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}
