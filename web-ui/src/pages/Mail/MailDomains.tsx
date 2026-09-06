import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Plus, Mail, Info } from 'lucide-react'
import { useInstanceStore } from '../../stores/instance'
import { useMailDomains, useDeleteMailDomain } from '../../hooks/useApi'
import {
  PageHeader,
  Card,
  DataTable,
  ConfirmDialog,
  EmptyState,
  QueryError,
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  buttonVariants,
  toast,
} from '../../components/ui'
import type { MailDomain } from '../../types'

export function MailDomains() {
  const { selectedInstanceId } = useInstanceStore()
  const navigate = useNavigate()
  const { data: domains, isLoading, isError, refetch } = useMailDomains(selectedInstanceId!)
  const deleteMutation = useDeleteMailDomain(selectedInstanceId!)
  const [deleteTarget, setDeleteTarget] = useState<MailDomain | null>(null)

  const handleDelete = async () => {
    if (!deleteTarget) return
    try {
      await deleteMutation.mutateAsync(deleteTarget.id)
      toast.success(`Mail domain "${deleteTarget.domain}" deleted`)
      setDeleteTarget(null)
    } catch {
      toast.error('Failed to delete mail domain')
    }
  }

  if (!selectedInstanceId) {
    return (
      <div>
        <PageHeader
          title="Mail Domains"
          description="Manage email domains, users, and security settings"
        />
        <Card className="mt-6">
          <div className="flex items-center gap-3 text-on-surface-muted">
            <Info className="h-5 w-5 shrink-0" />
            <p className="text-sm">Select an instance from the top bar to manage its mail domains.</p>
          </div>
        </Card>
      </div>
    )
  }

  const columns = [
    {
      key: 'domain',
      header: 'Domain',
      className: 'font-mono',
      render: (d: MailDomain) => (
        <span className="font-medium text-on-surface">{d.domain}</span>
      ),
    },
    {
      key: 'enabled',
      header: 'Status',
      render: (d: MailDomain) => (
        <span className={`inline-flex items-center gap-1.5 text-xs font-medium px-2 py-0.5 rounded-full ${d.enabled ? 'bg-success-subtle text-success' : 'bg-neutral-subtle text-on-surface-muted'}`}>
          {d.enabled ? 'Active' : 'Disabled'}
        </span>
      ),
    },
    {
      key: 'features',
      header: 'Features',
      render: (d: MailDomain) => (
        <div className="flex flex-wrap gap-1">
          {d.spam_filter_enabled && <span className="px-1.5 py-0.5 text-xs rounded bg-info-subtle text-info">Spam</span>}
          {d.virus_scan_enabled && <span className="px-1.5 py-0.5 text-xs rounded bg-danger-subtle text-danger">AV</span>}
          {d.dkim_enabled && <span className="px-1.5 py-0.5 text-xs rounded bg-success-subtle text-success">DKIM</span>}
          {d.llm_enabled && <span className="px-1.5 py-0.5 text-xs rounded bg-info-subtle text-info">LLM</span>}
          {d.groupware_enabled && <span className="px-1.5 py-0.5 text-xs rounded bg-warning-subtle text-warning">SOGo</span>}
        </div>
      ),
    },
  ]

  return (
    <div>
      <PageHeader
        title="Mail Domains"
        description="Manage email domains, users, and security settings"
        primaryAction={
          <Link to="/mail/domains/create" className={buttonVariants()}>
            <Plus className="w-4 h-4" />
            Add Domain
          </Link>
        }
      />

      {domains && domains.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6 mb-6">
          <Card>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-info-subtle rounded-card"><Mail className="w-5 h-5 text-info" /></div>
              <div><p className="text-sm text-on-surface-muted">Total Domains</p><p className="text-2xl font-bold text-on-surface">{domains.length}</p></div>
            </div>
          </Card>
          <Card>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-success-subtle rounded-card"><Mail className="w-5 h-5 text-success" /></div>
              <div><p className="text-sm text-on-surface-muted">Active</p><p className="text-2xl font-bold text-on-surface">{domains.filter((d) => d.enabled).length}</p></div>
            </div>
          </Card>
          <Card>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-info-subtle rounded-card"><Mail className="w-5 h-5 text-info" /></div>
              <div><p className="text-sm text-on-surface-muted">Spam Filter</p><p className="text-2xl font-bold text-on-surface">{domains.filter((d) => d.spam_filter_enabled).length}</p></div>
            </div>
          </Card>
          <Card>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-danger-subtle rounded-card"><Mail className="w-5 h-5 text-danger" /></div>
              <div><p className="text-sm text-on-surface-muted">Antivirus</p><p className="text-2xl font-bold text-on-surface">{domains.filter((d) => d.virus_scan_enabled).length}</p></div>
            </div>
          </Card>
        </div>
      )}

      {isError ? (
        <QueryError onRetry={() => refetch()} />
      ) : (
        <DataTable
          columns={columns}
          data={domains ?? []}
          keyExtractor={(d) => d.id}
          isLoading={isLoading}
          onRowClick={(d) => navigate(`/mail/domains/${d.id}`)}
          rowActions={(d) => (
            <DropdownMenu>
              <DropdownMenuTrigger />
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => navigate(`/mail/domains/${d.id}`)}>
                  View
                </DropdownMenuItem>
                <DropdownMenuItem
                  danger
                  onClick={() => setDeleteTarget(d)}
                >
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
          emptyContent={
            <EmptyState
              icon={Mail}
              title="No mail domains"
              description="Add your first email domain to get started."
              actionLabel="Add Domain"
              actionTo="/mail/domains/create"
            />
          }
        />
      )}

      <ConfirmDialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Delete Domain"
        message={`Are you sure you want to delete "${deleteTarget?.domain}"?`}
        impact={`Removes ${deleteTarget?.domain} including mailboxes and DNS records.`}
        loading={deleteMutation.isPending}
      />
    </div>
  )
}
