import { useState, useMemo } from 'react'
import { ClipboardList, RefreshCw } from 'lucide-react'
import { useAuditLogs, useUsers, useInstances } from '../hooks/useApi'
import { useAuthStore } from '../stores/auth'
import {
  PageHeader,
  Button,
  DataTable,
  Select,
  Input,
  EmptyState,
  Badge,
} from '../components/ui'
import { format } from 'date-fns'
import type { AuditLog } from '../types'

/* ── Action variant map ── */
const actionVariant: Record<string, 'success' | 'danger' | 'warning' | 'info' | 'neutral'> = {
  create: 'success',
  update: 'info',
  delete: 'danger',
  deploy: 'warning',
  login: 'neutral',
}

/* ── Resolve first token (e.g. "vpn.server.update" → "update") ── */
function actionLabel(raw: string): string {
  const last = raw.split('.').pop() ?? raw
  return last.charAt(0).toUpperCase() + last.slice(1)
}

export function AuditLogs() {
  const { user } = useAuthStore()
  const isAdmin = user?.role === 'admin' || user?.role === 'superadmin'

  /* ── Filter state (client-side; hook has no date params) ── */
  const [actionFilter, setActionFilter] = useState('')
  const [resourceFilter, setResourceFilter] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  /* ── Data fetching ── */
  const params: Record<string, unknown> = {}
  if (actionFilter) params.action = actionFilter
  if (resourceFilter) params.resource_type = resourceFilter

  const { data: logs, isLoading, isError, refetch } = useAuditLogs(params)
  const { data: users } = useUsers()
  const { data: instances } = useInstances()

  /* ── Resolution maps ── */
  const userMap = useMemo(() => {
    const m = new Map<number, string>()
    if (users) {
      for (const u of users) m.set(u.id, u.username)
    }
    return m
  }, [users])

  const instanceMap = useMemo(() => {
    const m = new Map<number, string>()
    if (instances) {
      for (const inst of instances) m.set(inst.id, inst.name)
    }
    return m
  }, [instances])

  /* ── Client-side date filtering ── */
  const filteredLogs = useMemo(() => {
    if (!logs) return []
    return logs.filter((log) => {
      if (dateFrom) {
        const ts = new Date(log.timestamp)
        const from = new Date(dateFrom)
        from.setHours(0, 0, 0, 0)
        if (ts < from) return false
      }
      if (dateTo) {
        const ts = new Date(log.timestamp)
        const to = new Date(dateTo)
        to.setHours(23, 59, 59, 999)
        if (ts > to) return false
      }
      return true
    })
  }, [logs, dateFrom, dateTo])

  /* ── Admin gate ── */
  if (!isAdmin) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Audit Logs"
          description="View system activity and change history."
        />
        <EmptyState
          icon={ClipboardList}
          title="Access Denied"
          description="You need admin privileges to view audit logs."
        />
      </div>
    )
  }

  /* ── Column defs ── */
  const columns = [
    {
      key: 'timestamp',
      header: 'Time',
      className: 'whitespace-nowrap',
      render: (log: AuditLog) => (
        <span className="font-mono text-xs text-on-surface-muted">
          {format(new Date(log.timestamp), 'yyyy-MM-dd HH:mm:ss')}
        </span>
      ),
    },
    {
      key: 'user',
      header: 'User',
      render: (log: AuditLog) => {
        if (!log.user_id) return <span className="text-sm text-on-surface-muted">System</span>
        const name = userMap.get(log.user_id)
        return (
          <span className="text-sm text-on-surface">
            {name ?? `User #${log.user_id} (unknown)`}
          </span>
        )
      },
    },
    {
      key: 'action',
      header: 'Action',
      render: (log: AuditLog) => {
        const lastToken = log.action.split('.').pop() ?? log.action
        const variant = actionVariant[lastToken] ?? 'neutral'
        return <Badge variant={variant}>{actionLabel(log.action)}</Badge>
      },
    },
    {
      key: 'resource',
      header: 'Resource',
      render: (log: AuditLog) => (
        <div className="flex items-center gap-1">
          <span className="text-sm font-medium text-on-surface">{log.resource_type}</span>
          {log.resource_id && (
            <span className="font-mono text-xs text-on-surface-muted">#{log.resource_id}</span>
          )}
        </div>
      ),
    },
    {
      key: 'instance',
      header: 'Instance',
      render: (log: AuditLog) => {
        if (!log.instance_id) return <span className="text-sm text-on-surface-muted">-</span>
        const name = instanceMap.get(log.instance_id)
        return (
          <span className="text-sm text-on-surface">
            {name ?? `Instance #${log.instance_id} (unknown)`}
          </span>
        )
      },
    },
    {
      key: 'summary',
      header: 'Summary',
      render: (log: AuditLog) => {
        const text = `${log.action} on ${log.resource_type}${log.resource_id ? ` #${log.resource_id}` : ''}`
        return (
          <span className="text-sm text-on-surface-muted truncate block max-w-xs" title={text}>
            {text}
          </span>
        )
      },
    },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title="Audit Logs"
        description="View system activity and change history."
        secondaryActions={[
          <Button key="refresh" variant="secondary" icon={RefreshCw} onClick={() => refetch()}>
            Refresh
          </Button>,
        ]}
      />

      {/* ── Filter toolbar ── */}
      <div className="rounded-card border border-border bg-surface-card p-4">
        <div className="flex flex-wrap items-center gap-4">
          <Select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            aria-label="Filter by action"
          >
            <option value="">All Actions</option>
            <option value="create">Create</option>
            <option value="update">Update</option>
            <option value="delete">Delete</option>
            <option value="deploy">Deploy</option>
            <option value="login">Login</option>
          </Select>
          <Select
            value={resourceFilter}
            onChange={(e) => setResourceFilter(e.target.value)}
            aria-label="Filter by resource"
          >
            <option value="">All Resources</option>
            <option value="firewall_rule">Firewall Rule</option>
            <option value="instance">Instance</option>
            <option value="user">User</option>
            <option value="mail_domain">Mail Domain</option>
            <option value="vpn_server">VPN Server</option>
            <option value="routing_rule">Routing Rule</option>
          </Select>
          <Input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            aria-label="Date from"
            className="w-auto"
          />
          <Input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            aria-label="Date to"
            className="w-auto"
          />
        </div>
      </div>

      <DataTable
        columns={columns}
        data={filteredLogs}
        keyExtractor={(log) => log.id}
        enableSorting
        searchable
        searchPlaceholder="Search audit logs..."
        pagination={{ pageSize: 25 }}
        isLoading={isLoading}
        isError={isError}
        onRetry={() => refetch()}
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
