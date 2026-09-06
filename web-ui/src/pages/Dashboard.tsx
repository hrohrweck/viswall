import { Link, useNavigate } from 'react-router-dom'
import { formatDistanceToNow } from 'date-fns'
import {
  Server,
  Shield,
  Network,
  Mail,
  RefreshCw,
  MoreVertical,
  CheckCircle2,
  ExternalLink,
} from 'lucide-react'
import {
  useInstances,
  useMetricsOverview,
  useAuditLogs,
} from '../hooks/useApi'
import { useAuthStore } from '../stores/auth'
import {
  PageHeader,
  Card,
  CardBody,
  Button,
  IconButton,
  DataTable,
  StatusBadge,
  Skeleton,
} from '../components/ui'
import type { Column } from '../components/ui/DataTable'
import type { Instance } from '../types'
import { useQueryClient } from '@tanstack/react-query'
import { cn } from '../lib/utils'

/* -------------------------------------------------------------------------- */
/*  Static status-class map — zero dynamic/template-literal classNames         */
/* -------------------------------------------------------------------------- */

const statusCardClasses: Record<string, { bg: string; text: string }> = {
  primary: { bg: 'bg-primary-subtle', text: 'text-primary' },
  success: { bg: 'bg-success-subtle', text: 'text-success' },
  warning: { bg: 'bg-warning-subtle', text: 'text-warning' },
  danger: { bg: 'bg-danger-subtle', text: 'text-danger' },
}

/* -------------------------------------------------------------------------- */
/*  Health table columns                                                       */
/* -------------------------------------------------------------------------- */

const healthColumns: Column<Instance>[] = [
  {
    key: 'name',
    header: 'Instance',
    render: (row) => (
      <span className="font-medium text-on-surface">{row.name}</span>
    ),
  },
  {
    key: 'hostname',
    header: 'Hostname',
    className: 'font-mono text-xs',
  },
  {
    key: 'status',
    header: 'Status',
    render: (row) => <StatusBadge status={row.status} />,
  },
  {
    key: 'cpu',
    header: 'CPU',
    render: () => <span className="text-on-surface-muted">&mdash;</span>,
  },
  {
    key: 'memory',
    header: 'Memory',
    render: () => <span className="text-on-surface-muted">&mdash;</span>,
  },
  {
    key: 'last_seen',
    header: 'Last seen',
    render: (row) =>
      row.last_seen ? (
        formatDistanceToNow(new Date(row.last_seen), { addSuffix: true })
      ) : (
        <span className="text-on-surface-muted">Never</span>
      ),
  },
]

/* -------------------------------------------------------------------------- */
/*  Dashboard                                                                  */
/* -------------------------------------------------------------------------- */

export function Dashboard() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { data: instances, isLoading: instancesLoading } = useInstances()
  const { data: overview, isLoading: overviewLoading } = useMetricsOverview()
  const { data: auditLogs } = useAuditLogs({ limit: 3 })
  const user = useAuthStore((s) => s.user)
  const isAdmin = user?.role === 'superadmin' || user?.role === 'admin'

  const isLoading = instancesLoading || overviewLoading

  const activeCount = instances?.filter((i) => i.status === 'active').length ?? 0

  const stats = [
    {
      label: 'Total instances',
      value: overview?.instances ?? 0,
      detail: `${activeCount} active`,
      icon: Server,
      color: 'primary',
      to: '/instances',
    },
    {
      label: 'Firewall rules',
      value: overview?.firewall_rules ?? 0,
      detail: 'Across all instances',
      icon: Shield,
      color: 'success',
      to: '/firewall',
    },
    {
      label: 'VPN servers',
      value: overview?.vpn_servers ?? 0,
      detail: 'Across all instances',
      icon: Network,
      color: 'warning',
      to: '/vpn',
    },
    {
      label: 'Mail domains',
      value: overview?.mail_domains ?? 0,
      detail: 'Across all instances',
      icon: Mail,
      color: 'danger',
      to: '/mail',
    },
  ]

  /* Attention-needed: offline or maintenance instances */
  const attentionInstances =
    instances?.filter((i) => {
      const s = i.status as string
      return s === 'maintenance' || s === 'error' || s === 'offline'
    }) ?? []

  return (
    <div className="flex flex-col gap-6">
      {/* ── Header ────────────────────────────────────────────────────── */}
      <PageHeader
        title="Dashboard"
        description="Overview of your infrastructure and recent activity."
        secondaryActions={[
          <IconButton
            key="refresh"
            icon={RefreshCw}
            label="Refresh"
            variant="secondary"
            onClick={() => queryClient.invalidateQueries()}
          />,
        ]}
      />

      {/* ── Stat cards ────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map(({ label, value, detail, icon: Icon, color, to }) => {
          const cls = statusCardClasses[color]
          return (
            <Link
              key={label}
              to={to}
              className="rounded-card border border-border bg-surface-card p-5 hover:bg-surface-elevated transition-colors"
            >
              <div className="flex items-start justify-between mb-3">
                <span className="text-sm text-on-surface-muted">{label}</span>
                <div className={cn('flex h-9 w-9 items-center justify-center rounded-card', cls.bg)}>
                  <Icon className={cn('h-4.5 w-4.5', cls.text)} />
                </div>
              </div>
              {isLoading ? (
                <Skeleton className="h-7 w-16 mb-1" />
              ) : (
                <p className="text-2xl font-semibold text-on-surface">{value}</p>
              )}
              <p className="text-xs text-on-surface-muted mt-0.5">{detail}</p>
            </Link>
          )
        })}
      </div>

      {/* ── Instance health table ─────────────────────────────────────── */}
      <Card title="Instance health">
        <CardBody padding="p-0">
          <DataTable
            columns={healthColumns}
            data={instances ?? []}
            keyExtractor={(i) => i.id}
            enableSorting
            isLoading={instancesLoading}
            onRowClick={(i) => navigate(`/instances/${i.id}`)}
            rowActions={(i) => (
              <IconButton
                icon={MoreVertical}
                label="Actions"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation()
                  navigate(`/instances/${i.id}`)
                }}
              />
            )}
          />
        </CardBody>
      </Card>

      {/* ── Bottom row: Attention + Recent activity ───────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Attention needed */}
        <Card title="Attention needed">
          <CardBody>
            {attentionInstances.length === 0 ? (
              <div className="flex items-center gap-2 py-3 text-sm text-on-surface-muted">
                <CheckCircle2 className="h-4 w-4 text-success" />
                All systems nominal
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                {attentionInstances.map((instance) => (
                  <div
                    key={instance.id}
                    className="flex items-center justify-between"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <StatusBadge status={instance.status} />
                      <span className="text-sm font-medium text-on-surface truncate">
                        {instance.name}
                      </span>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      icon={ExternalLink}
                      onClick={() => navigate(`/instances/${instance.id}`)}
                    >
                      View
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardBody>
        </Card>

        {/* Recent activity — admin-only */}
        {isAdmin && (
          <Card title="Recent activity">
            <CardBody>
              {auditLogs && auditLogs.length > 0 ? (
                <div className="flex flex-col gap-3">
                  {auditLogs.slice(0, 3).map((log) => (
                    <div
                      key={log.id}
                      className="flex items-center justify-between gap-3"
                    >
                      <div className="min-w-0">
                        <p className="text-sm text-on-surface truncate">
                          {log.action}
                        </p>
                        <p className="text-xs text-on-surface-muted">
                          {log.resource_type}
                          {log.resource_id ? ` #${log.resource_id}` : ''}
                        </p>
                      </div>
                      <span className="text-xs text-on-surface-muted whitespace-nowrap">
                        {formatDistanceToNow(new Date(log.timestamp), {
                          addSuffix: true,
                        })}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-on-surface-muted py-3">
                  No recent activity.
                </p>
              )}
            </CardBody>
          </Card>
        )}
      </div>
    </div>
  )
}
