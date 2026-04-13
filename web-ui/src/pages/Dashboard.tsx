import { Link } from 'react-router-dom'
import { Server, Shield, Mail, Network, Plus, ArrowRight } from 'lucide-react'
import { useInstances } from '../hooks/useApi'
import { LoadingSpinner, StatusBadge } from '../components/ui'
import { formatDistanceToNow } from 'date-fns'

export function Dashboard() {
  const { data: instances, isLoading } = useInstances()

  if (isLoading) return <LoadingSpinner />

  const instanceCount = instances?.length ?? 0
  const activeInstances = instances?.filter((i) => i.status === 'active').length ?? 0

  const stats = [
    { label: 'Instances', value: instanceCount, icon: Server, color: 'blue', detail: `${activeInstances} active` },
    { label: 'Firewall Rules', value: '-', icon: Shield, color: 'green', detail: 'Per instance' },
    { label: 'VPN Servers', value: '-', icon: Network, color: 'indigo', detail: 'Per instance' },
    { label: 'Mail Domains', value: '-', icon: Mail, color: 'purple', detail: 'Per instance' },
  ]

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map(({ label, value, icon: Icon, color, detail }) => (
          <div key={label} className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{label}</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
                <p className="text-xs text-gray-400 mt-1">{detail}</p>
              </div>
              <div className={`p-3 bg-${color}-100 rounded-lg`}>
                <Icon className={`w-6 h-6 text-${color}-600`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">System Status</h3>
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
                  className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50"
                >
                  <div className="flex items-center gap-3">
                    <Server className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="font-medium text-gray-900">{instance.name}</p>
                      <p className="text-xs text-gray-500">{instance.hostname}</p>
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
              <Server className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-600 mb-4">No instances connected yet.</p>
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

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
          <div className="grid grid-cols-2 gap-3">
            <Link
              to="/instances"
              className="flex flex-col items-center gap-2 p-4 rounded-lg border border-gray-200 hover:bg-gray-50 hover:border-primary-300 transition-colors"
            >
              <Server className="w-6 h-6 text-blue-600" />
              <span className="text-sm font-medium text-gray-700">Manage Instances</span>
            </Link>
            <Link
              to="/firewall"
              className="flex flex-col items-center gap-2 p-4 rounded-lg border border-gray-200 hover:bg-gray-50 hover:border-primary-300 transition-colors"
            >
              <Shield className="w-6 h-6 text-green-600" />
              <span className="text-sm font-medium text-gray-700">Firewall Rules</span>
            </Link>
            <Link
              to="/vpn"
              className="flex flex-col items-center gap-2 p-4 rounded-lg border border-gray-200 hover:bg-gray-50 hover:border-primary-300 transition-colors"
            >
              <Network className="w-6 h-6 text-indigo-600" />
              <span className="text-sm font-medium text-gray-700">VPN Servers</span>
            </Link>
            <Link
              to="/mail"
              className="flex flex-col items-center gap-2 p-4 rounded-lg border border-gray-200 hover:bg-gray-50 hover:border-primary-300 transition-colors"
            >
              <Mail className="w-6 h-6 text-purple-600" />
              <span className="text-sm font-medium text-gray-700">Mail Domains</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
