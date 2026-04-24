import { useState } from 'react'
import {
  BarChart3,
  Cpu,
  HardDrive,
  MemoryStick,
  Network,
  Mail,
  Activity,
  ArrowUpDown,
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
import { InstanceSelector, LoadingSpinner, EmptyState } from '../components/ui'

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

export function Metrics() {
  const { selectedInstanceId } = useInstanceStore()
  const [timeRange, setTimeRange] = useState<'1h' | '24h' | '7d'>('24h')

  const { data: latest, isLoading: latestLoading } = useMetricsLatest(
    selectedInstanceId ?? 0
  )
  const { data: dashboard, isLoading: dashboardLoading } = useDashboardData(
    selectedInstanceId ?? 0
  )

  // Calculate time range for historical query
  const now = new Date()
  const startTimeMap = {
    '1h': new Date(now.getTime() - 60 * 60 * 1000),
    '24h': new Date(now.getTime() - 24 * 60 * 60 * 1000),
    '7d': new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000),
  }

  const { data: historical } = useMetricsQuery(
    {
      instance_ids: selectedInstanceId ? [selectedInstanceId] : undefined,
      start_time: startTimeMap[timeRange].toISOString(),
      end_time: now.toISOString(),
      granularity: '5m',
    },
    { enabled: !!selectedInstanceId }
  )

  const isLoading = latestLoading || dashboardLoading

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

  if (!selectedInstanceId) {
    return (
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Metrics</h2>
        <EmptyState
          icon={BarChart3}
          title="Select an Instance"
          description="Choose an instance to view metrics."
        />
        <div className="mt-4">
          <InstanceSelector />
        </div>
      </div>
    )
  }

  if (isLoading) return <LoadingSpinner />

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

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Metrics</h2>
        <InstanceSelector />
      </div>

      {/* Count Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Activity className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Firewall Rules</p>
              <p className="text-2xl font-bold">{counts?.firewall_rule_count ?? 0}</p>
            </div>
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Mail className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Mail Domains</p>
              <p className="text-2xl font-bold">{counts?.mail_domain_count ?? 0}</p>
            </div>
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-100 rounded-lg">
              <Network className="w-5 h-5 text-indigo-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">VPN Servers</p>
              <p className="text-2xl font-bold">{counts?.vpn_server_count ?? 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* System Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {statCards.map(({ label, value, icon: Icon, color, detail }) => (
          <div key={label} className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center gap-3">
              <div className={`p-2 bg-${color}-100 rounded-lg`}>
                <Icon className={`w-5 h-5 text-${color}-600`} />
              </div>
              <div>
                <p className="text-sm text-gray-600">{label}</p>
                <p className="text-2xl font-bold">{value}</p>
                <p className="text-xs text-gray-400">{detail}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Time Range Selector */}
      <div className="flex items-center gap-2 mb-4">
        <span className="text-sm text-gray-600">Time Range:</span>
        {(['1h', '24h', '7d'] as const).map((range) => (
          <button
            key={range}
            onClick={() => setTimeRange(range)}
            className={`px-3 py-1 text-sm rounded-lg ${
              timeRange === range
                ? 'bg-primary-600 text-white'
                : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50'
            }`}
          >
            {range === '1h' ? '1 Hour' : range === '24h' ? '24 Hours' : '7 Days'}
          </button>
        ))}
      </div>

      {/* Charts */}
      {chartData.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              System Resources
            </h3>
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis unit="%" />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="cpu"
                  stroke="#3b82f6"
                  fill="#93c5fd"
                  name="CPU %"
                />
                <Area
                  type="monotone"
                  dataKey="memory"
                  stroke="#a855f7"
                  fill="#d8b4fe"
                  name="Memory %"
                />
                <Area
                  type="monotone"
                  dataKey="disk"
                  stroke="#f97316"
                  fill="#fdba74"
                  name="Disk %"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Mail Activity
            </h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={mailChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="inbound" fill="#3b82f6" name="Inbound" />
                <Bar dataKey="outbound" fill="#22c55e" name="Outbound" />
                <Bar dataKey="spam" fill="#ef4444" name="Spam" />
                <Bar dataKey="virus" fill="#f97316" name="Virus" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      ) : (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mb-6">
          <EmptyState
            icon={BarChart3}
            title="No Historical Data"
            description="Metrics snapshots will appear here once the metrics collector is running."
          />
        </div>
      )}

      {/* Network Interfaces */}
      {system?.interface_stats && system.interface_stats.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              Network Interfaces
            </h3>
          </div>
          <div className="divide-y divide-gray-200">
            {system.interface_stats.map((iface) => (
              <div
                key={iface.name}
                className="px-6 py-4 flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <Network className="w-5 h-5 text-gray-400" />
                  <span className="font-medium text-gray-900">{iface.name}</span>
                </div>
                <div className="flex items-center gap-6 text-sm text-gray-600">
                  <div className="flex items-center gap-1">
                    <ArrowUpDown className="w-4 h-4 text-green-500" />
                    <span>RX: {formatBytes(iface.rx_bytes)}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <ArrowUpDown className="w-4 h-4 text-blue-500" />
                    <span>TX: {formatBytes(iface.tx_bytes)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
