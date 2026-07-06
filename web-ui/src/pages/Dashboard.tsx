import { Link } from 'react-router-dom'
import { Server, Shield, Mail, Network, Plus, ArrowRight } from 'lucide-react'
import { useInstances, useMetricsOverview } from '../hooks/useApi'
import { LoadingSpinner, StatusBadge } from '../components/ui'
import { formatDistanceToNow } from 'date-fns'

export function Dashboard() {
  const { data: instances, isLoading: instancesLoading } = useInstances()
  const { data: overview, isLoading: overviewLoading } = useMetricsOverview()

  const isLoading = instancesLoading || overviewLoading

  if (isLoading) return <LoadingSpinner />

  const instanceCount = instances?.length ?? 0
  const activeInstances = instances?.filter((i) => i.status === 'active').length ?? 0

  const stats = [
    {
      label: 'Instances',
      value: instanceCount,
      icon: Server,
      color: 'blue',
      detail: `${activeInstances} active`,
    },
    {
      label: 'Firewall Rules',
      value: overview?.firewall_rules ?? 0,
      icon: Shield,
      color: 'green',
      detail: 'Across all instances',
    },
    {
      label: 'VPN Servers',
      value: overview?.vpn_servers ?? 0,
      icon: Network,
      color: 'indigo',
      detail: 'Across all instances',
    },
    {
      label: 'Mail Domains',
      value: overview?.mail_domains ?? 0,
      icon: Mail,
      color: 'purple',
      detail: 'Across all instances',
    },
  ]

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6 dark:text-white">Dashboard</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map(({ label, value, icon: Icon, color, detail }) => (
          <div key={label} className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 dark:bg-gray-900 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{label}</p>
                <p className="text-3xl font-bold text-gray-900 mt-1 dark:text-white">{value}</p>
                <p className="text-xs text-gray-400 mt-1 dark:text-gray-500">{detail}</p>
              </div>
              <div className={`p-3 bg-${color}-100 rounded-lg dark:bg-gray-800`}>
                <Icon className={`w-6 h-6 text-${color}-600 dark:text-gray-300`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 dark:bg-gray-900 dark:border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">System Status</h3>
            <Link to="/instances" className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1">
              View all <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          {instances && instances.length > 0 ? (
            <div className="space-y-3">
              {instances.map((instance) => (
                <Link
                  key={instance.id}
                  to={`/instances/${instance.id}`}
                  className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800"
                >
                  <div className="flex items-center gap-3">
                    <Server className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">{instance.name}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">{instance.hostname}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {instance.last_seen && (
                      <span className="text-xs text-gray-400">
                        {formatDistanceToNow(new Date(instance.last_seen), { addSuffix: true })}
                      </span>
                    )}
                    <StatusBadge status={instance.status} />
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-center py-6">
              <Server className="w-12 h-12 text-gray-300 mx-auto mb-3 dark:text-gray-600" />
              <p className="text-gray-600 dark:text-gray-400 mb-4">No instances connected yet.</p>
              <Link
                to="/instances"
                className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm"
              >
                <Plus className="w-4 h-4" />
                Add Instance
              </Link>
            </div>
          )}
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 dark:bg-gray-900 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 dark:text-white">Quick Actions</h3>
          <div className="grid grid-cols-2 gap-3">
            <Link
              to="/instances"
              className="flex flex-col items-center gap-2 p-4 rounded-lg border border-gray-200 hover:bg-gray-50 hover:border-primary-300 transition-colors dark:border-gray-700 dark:hover:bg-gray-800"
            >
              <Server className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Manage Instances</span>
            </Link>
            <Link
              to="/firewall"
              className="flex flex-col items-center gap-2 p-4 rounded-lg border border-gray-200 hover:bg-gray-50 hover:border-primary-300 transition-colors dark:border-gray-700 dark:hover:bg-gray-800"
            >
              <Shield className="w-6 h-6 text-green-600 dark:text-green-400" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Firewall Rules</span>
            </Link>
            <Link
              to="/vpn"
              className="flex flex-col items-center gap-2 p-4 rounded-lg border border-gray-200 hover:bg-gray-50 hover:border-primary-300 transition-colors dark:border-gray-700 dark:hover:bg-gray-800"
            >
              <Network className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">VPN Servers</span>
            </Link>
            <Link
              to="/mail"
              className="flex flex-col items-center gap-2 p-4 rounded-lg border border-gray-200 hover:bg-gray-50 hover:border-primary-300 transition-colors dark:border-gray-700 dark:hover:bg-gray-800"
            >
              <Mail className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Mail Domains</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
