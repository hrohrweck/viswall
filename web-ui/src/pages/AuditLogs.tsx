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
  start: 'success',
  stop: 'danger',
  restart: 'warning',
  enable_groupware: 'success',
  disable_groupware: 'danger',
}

/* ── Resolve first token (e.g. "vpn.server.update" → "update") ── */
function actionLabel(raw: string): string {
  const last = raw.split('.').pop() ?? raw
  return last.charAt(0).toUpperCase() + last.slice(1)
}

export function AuditLogs() {
  const { user } = useAuthStore()
  const isAdmin = user?.role === 'admin' || user?.role === 'superadmin'

  /* ── Filter state (server-side; backend supports action/resource/date params) ── */
  const [actionFilter, setActionFilter] = useState('')
  const [resourceFilter, setResourceFilter] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  /* ── Data fetching ── */
  const params: Record<string, unknown> = { limit: 500 }
  if (actionFilter) params.action = actionFilter
  if (resourceFilter) params.resource_type = resourceFilter
  if (dateFrom) params.start_time = new Date(`${dateFrom}T00:00:00`).toISOString()
  if (dateTo) params.end_time = new Date(`${dateTo}T23:59:59.999`).toISOString()

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
        const leaf = log.action.split('.').pop() ?? log.action
        const variant = actionVariant[leaf] ?? 'neutral'
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
            <option value="start">Start</option>
            <option value="stop">Stop</option>
            <option value="restart">Restart</option>
            <option value="enable_groupware">Enable Groupware</option>
            <option value="disable_groupware">Disable Groupware</option>
          </Select>
          <Select
            value={resourceFilter}
            onChange={(e) => setResourceFilter(e.target.value)}
            aria-label="Filter by resource"
          >
            <option value="">All Resources</option>
            <option value="instance">Instance</option>
            <option value="user">User</option>
            <option value="firewall_rule">Firewall Rule</option>
            <option value="routing_rule">Routing Rule</option>
            <option value="vpn_server">VPN Server</option>
            <option value="mail_domain">Mail Domain</option>
            <option value="dns_server">DNS Server</option>
            <option value="dns_zone">DNS Zone</option>
            <option value="dns_zone_dnssec">DNSSEC</option>
            <option value="dns_tsig_key">TSIG Key</option>
            <option value="dhcp_server">DHCP Server</option>
            <option value="dhcp_subnet">DHCP Subnet</option>
            <option value="dhcp_pool">DHCP Pool</option>
            <option value="dhcp_reservation">DHCP Reservation</option>
            <option value="dhcp_option">DHCP Option</option>
            <option value="dhcp_lease">DHCP Lease</option>
            <option value="firewall_agent">Firewall Agent</option>
            <option value="vpn_agent">VPN Agent</option>
            <option value="dns_agent">DNS Agent</option>
            <option value="dhcp_agent">DHCP Agent</option>
            <option value="mail_agent">Mail Agent</option>
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
        data={logs ?? []}
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
