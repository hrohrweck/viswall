import { useState } from 'react'
import { ClipboardList, Filter, RefreshCw } from 'lucide-react'
import { useAuditLogs } from '../hooks/useApi'
import { useAuthStore } from '../stores/auth'
import {
  DataTable,
  LoadingSpinner,
  EmptyState,
} from '../components/ui'
import { formatDistanceToNow } from 'date-fns'
import type { AuditLog } from '../types'

const actionColors: Record<string, string> = {
  create: 'bg-green-100 text-green-700 dark:bg-green-950/30 dark:text-green-400',
  update: 'bg-blue-100 text-blue-700 dark:bg-blue-950/30 dark:text-blue-400',
  delete: 'bg-red-100 text-red-700 dark:bg-red-950/30 dark:text-red-400',
  deploy: 'bg-purple-100 text-purple-700 dark:bg-purple-950/30 dark:text-purple-400',
  login: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
}

export function AuditLogs() {
  const { user } = useAuthStore()
  const isAdmin = user?.role === 'admin' || user?.role === 'superadmin'

  const [filters, setFilters] = useState({
    action: '',
    resource_type: '',
    limit: 50,
  })

  const params: Record<string, unknown> = { limit: filters.limit }
  if (filters.action) params.action = filters.action
  if (filters.resource_type) params.resource_type = filters.resource_type

  const { data: logs, isLoading, refetch } = useAuditLogs(params)

  if (!isAdmin) {
    return (
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6 dark:text-white">Audit Logs</h2>
        <EmptyState
          icon={ClipboardList}
          title="Access Denied"
          description="You need admin privileges to view audit logs."
        />
      </div>
    )
  }

  if (isLoading) return <LoadingSpinner />

  const columns = [
    {
      key: 'timestamp',
      header: 'Time',
      render: (log: AuditLog) => (
        <span className="text-sm text-gray-600 whitespace-nowrap dark:text-gray-400">
          {formatDistanceToNow(new Date(log.timestamp), { addSuffix: true })}
        </span>
      ),
    },
    {
      key: 'action',
      header: 'Action',
      render: (log: AuditLog) => (
        <span className={`px-2 py-0.5 rounded text-xs font-medium capitalize ${actionColors[log.action] || 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'}`}>
          {log.action}
        </span>
      ),
    },
    {
      key: 'resource',
      header: 'Resource',
      render: (log: AuditLog) => (
        <div>
          <span className="text-sm font-medium text-gray-900 dark:text-white">{log.resource_type}</span>
          {log.resource_id && (
            <span className="text-xs text-gray-500 ml-1 dark:text-gray-500">#{log.resource_id}</span>
          )}
        </div>
      ),
    },
    {
      key: 'user',
      header: 'User',
      render: (log: AuditLog) => (
        <span className="text-sm text-gray-600 dark:text-gray-400">
          {log.user_id ? `User #${log.user_id}` : 'System'}
        </span>
      ),
    },
    {
      key: 'instance',
      header: 'Instance',
      render: (log: AuditLog) => (
        <span className="text-sm text-gray-600 dark:text-gray-400">
          {log.instance_id ? `#${log.instance_id}` : '-'}
        </span>
      ),
    },
    {
      key: 'ip',
      header: 'IP Address',
      render: (log: AuditLog) => (
        <span className="text-sm text-gray-500 font-mono dark:text-gray-500">{log.ip_address || '-'}</span>
      ),
    },
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Audit Logs</h2>
        <div className="flex items-center gap-2">
          <button
            onClick={() => refetch()}
            className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 text-sm dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-700"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 mb-6 dark:bg-gray-900 dark:border-gray-700">
        <div className="flex items-center gap-4">
          <Filter className="w-4 h-4 text-gray-400 dark:text-gray-500" />
          <select
            value={filters.action}
            onChange={(e) => setFilters({ ...filters, action: e.target.value })}
            className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm dark:bg-gray-800 dark:border-gray-700 dark:text-white"
          >
            <option value="">All Actions</option>
            <option value="create">Create</option>
            <option value="update">Update</option>
            <option value="delete">Delete</option>
            <option value="deploy">Deploy</option>
            <option value="login">Login</option>
          </select>
          <select
            value={filters.resource_type}
            onChange={(e) => setFilters({ ...filters, resource_type: e.target.value })}
            className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm dark:bg-gray-800 dark:border-gray-700 dark:text-white"
          >
            <option value="">All Resources</option>
            <option value="firewall_rule">Firewall Rule</option>
            <option value="instance">Instance</option>
            <option value="user">User</option>
            <option value="mail_domain">Mail Domain</option>
            <option value="vpn_server">VPN Server</option>
            <option value="routing_rule">Routing Rule</option>
          </select>
        </div>
      </div>

      <DataTable
        columns={columns}
        data={logs || []}
        keyExtractor={(log) => log.id}
        emptyContent={
          <EmptyState
            icon={ClipboardList}
            title="No Audit Logs"
            description="Audit logs will appear here once actions are performed."
          />
        }
      />
    </div>
  )
}
