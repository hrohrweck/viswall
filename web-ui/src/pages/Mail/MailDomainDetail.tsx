import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { Key, Trash2, Users, Brain, Globe } from 'lucide-react'
import { useInstanceStore } from '../../stores/instance'
import {
  useMailDomain,
  useMailUsers,
  useCreateMailUser,
  useDeleteMailUser,
  useDeleteMailDomain,
  useRegenerateDkim,
  useGroupwareStatus,
  useEnableGroupware,
  useDisableGroupware,
  useGroupwareStats,
} from '../../hooks/useApi'
import {
  PageHeader,
  Tabs,
  Card,
  DataTable,
  Modal,
  ConfirmDialog,
  EmptyState,
  Skeleton,
  QueryError,
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  Badge,
  Switch,
  toast,
  buttonVariants,
} from '../../components/ui'
import { TabsContent } from '../../components/ui/Tabs'
import type { MailUser } from '../../types'
import { formatBytes } from '../../utils/format'
import { MailClassificationView } from './MailClassificationView'
import { MailboxForm } from '../../components/forms/MailboxForm'

export function MailDomainDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { selectedInstanceId } = useInstanceStore()
  const domainId = Number(id)
  const { data: domain, isLoading, isError, refetch } = useMailDomain(selectedInstanceId!, domainId)
  const { data: users } = useMailUsers(selectedInstanceId!, domainId)
  const deleteDomainMutation = useDeleteMailDomain(selectedInstanceId!)
  const createMutation = useCreateMailUser(selectedInstanceId!, domainId)
  const deleteMutation = useDeleteMailUser(selectedInstanceId!, domainId)
  const dkimMutation = useRegenerateDkim(selectedInstanceId!)
  const { data: groupwareStatus } = useGroupwareStatus(domainId)
  const enableGroupware = useEnableGroupware(domainId)
  const disableGroupware = useDisableGroupware(domainId)
  const { data: groupwareStats } = useGroupwareStats(domainId)

  const [showDeleteDomain, setShowDeleteDomain] = useState(false)
  const [showCreateUser, setShowCreateUser] = useState(false)
  const [deleteUserTarget, setDeleteUserTarget] = useState<MailUser | null>(null)
  const [showDkimConfirm, setShowDkimConfirm] = useState(false)
  const [showGroupwareConfirm, setShowGroupwareConfirm] = useState(false)
  const [activeTab, setActiveTab] = useState('users')

  if (isLoading) return <div className="space-y-4"><Skeleton className="h-8 w-64" /><Skeleton className="h-48" /></div>
  if (!domain) {
    return (
      <div>
        <Link to="/mail" className={buttonVariants({ variant: 'ghost', size: 'sm' }) + ' mb-4'}>
          ← Back to Mail Domains
        </Link>
        <EmptyState icon={Users} title="Domain not found" description="The mail domain you're looking for doesn't exist or has been removed." actionLabel="Back to Mail Domains" actionTo="/mail" />
      </div>
    )
  }

  const handleCreateUser = async (values: { username: string; full_name?: string; password?: string }) => {
    await createMutation.mutateAsync(values)
    toast.success(`Mailbox "${values.username}@${domain.domain}" created`)
    setShowCreateUser(false)
  }

  const handleDeleteDomain = async () => {
    await deleteDomainMutation.mutateAsync(domain.id)
    toast.success(`Domain "${domain.domain}" deleted`)
    navigate('/mail')
  }

  const handleDeleteUser = async () => {
    if (!deleteUserTarget) return
    await deleteMutation.mutateAsync(deleteUserTarget.id)
    toast.success(`Mailbox "${deleteUserTarget.username}" deleted`)
    setDeleteUserTarget(null)
  }

  const handleDkimRegenerate = async () => {
    await dkimMutation.mutateAsync(domain.id)
    toast.success('DKIM key regenerated — update your DNS record')
    setShowDkimConfirm(false)
  }

  const handleGroupwareToggle = async () => {
    if (domain.groupware_enabled) {
      await disableGroupware.mutateAsync()
      toast.success('SOGo groupware disabled')
    } else {
      await enableGroupware.mutateAsync()
      toast.success('SOGo groupware enabled')
    }
    setShowGroupwareConfirm(false)
  }

  const userColumns = [
    {
      key: 'username',
      header: 'Address',
      className: 'font-mono',
      render: (user: MailUser) => (
        <span className="font-medium text-on-surface">{user.username}@{domain.domain}</span>
      ),
    },
    {
      key: 'quota',
      header: 'Quota',
      render: (user: MailUser) => (
        <span className="text-sm text-on-surface-muted">{formatBytes(user.quota_used)} / {formatBytes(user.quota_bytes)}</span>
      ),
    },
    {
      key: 'enabled',
      header: 'Active',
      render: (user: MailUser) => <Switch checked={user.enabled} disabled aria-label={`Active: ${user.username}`} />,
    },
  ]

  const tabItems = [
    { value: 'users', label: `Mailboxes (${users?.length ?? 0})` },
    { value: 'classification', label: 'Classification' },
    { value: 'groupware', label: 'Groupware' },
  ]

  return (
    <div>
      <Link to="/mail" className={buttonVariants({ variant: 'ghost', size: 'sm' }) + ' mb-4'}>
        ← Back to Mail Domains
      </Link>

      <PageHeader
        title={domain.domain}
        description={`Instance ${domain.instance_id}`}
        primaryAction={
          <DropdownMenu>
            <DropdownMenuTrigger label="Domain actions" />
            <DropdownMenuContent>
              <DropdownMenuItem onClick={() => setShowDkimConfirm(true)}>
                <Key className="w-4 h-4 mr-2" />
                Regenerate DKIM
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setShowGroupwareConfirm(true)}>
                <Globe className="w-4 h-4 mr-2" />
                {domain.groupware_enabled ? 'Disable' : 'Enable'} Groupware
              </DropdownMenuItem>
              <DropdownMenuItem danger onClick={() => setShowDeleteDomain(true)}>
                <Trash2 className="w-4 h-4 mr-2" />
                Delete Domain
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        }
        tabs={
          <Tabs items={tabItems} value={activeTab} onValueChange={setActiveTab}>
            <TabsContent value="users">
              <div className="flex items-center justify-between mb-4 mt-4">
                <div />
                <button
                  onClick={() => setShowCreateUser(true)}
                  className={buttonVariants({ size: 'sm' })}
                >
                  <Users className="w-4 h-4" />
                  Add Mailbox
                </button>
              </div>
              <DataTable
                columns={userColumns}
                data={users || []}
                keyExtractor={(u) => u.id}
                searchable
                searchPlaceholder="Search mailboxes…"
                rowActions={(user) => (
                  <DropdownMenu>
                    <DropdownMenuTrigger />
                    <DropdownMenuContent>
                      <DropdownMenuItem danger onClick={() => setDeleteUserTarget(user)}>
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                )}
                emptyContent={<EmptyState icon={Users} title="No mailboxes" description="Create the first mailbox for this domain." actionLabel="Add Mailbox" onAction={() => setShowCreateUser(true)} />}
              />
            </TabsContent>

            <TabsContent value="classification">
              <div className="mt-4">
                <MailClassificationView domainId={domainId} />
              </div>
            </TabsContent>

            <TabsContent value="groupware">
              <div className="space-y-6 mt-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-on-surface">SOGo Groupware</h3>
                  <div className="flex items-center gap-3">
                    <span className={`text-sm font-medium ${domain.groupware_enabled ? 'text-success' : 'text-on-surface-muted'}`}>
                      {domain.groupware_enabled ? 'Enabled' : 'Disabled'}
                    </span>
                    <Switch
                      checked={domain.groupware_enabled}
                      onCheckedChange={() => setShowGroupwareConfirm(true)}
                      aria-label="Toggle groupware"
                    />
                  </div>
                </div>

                {groupwareStatus?.sogo_url && (
                  <Card>
                    <p className="text-sm text-on-surface-muted">
                      SOGo is accessible at <a href={groupwareStatus.sogo_url} className="font-medium text-primary underline">{groupwareStatus.sogo_url}</a>
                    </p>
                  </Card>
                )}

                {groupwareStats && domain.groupware_enabled && (
                  <div className="grid grid-cols-3 gap-4">
                    <Card>
                      <p className="text-sm text-on-surface-muted">Calendars</p>
                      <p className="text-2xl font-semibold text-on-surface">{(groupwareStats.calendars as number) || 0}</p>
                    </Card>
                    <Card>
                      <p className="text-sm text-on-surface-muted">Contacts</p>
                      <p className="text-2xl font-semibold text-on-surface">{(groupwareStats.contacts as number) || 0}</p>
                    </Card>
                    <Card>
                      <p className="text-sm text-on-surface-muted">Active Users</p>
                      <p className="text-2xl font-semibold text-on-surface">{(groupwareStats.active_users as number) || 0}</p>
                    </Card>
                  </div>
                )}
              </div>
            </TabsContent>
          </Tabs>
        }
      />

      <Modal open={showCreateUser} onClose={() => setShowCreateUser(false)} title="Add Mailbox">
        <MailboxForm
          domain={domain.domain}
          loading={createMutation.isPending}
          onSubmit={handleCreateUser}
          onCancel={() => setShowCreateUser(false)}
        />
      </Modal>

      <ConfirmDialog open={!!deleteUserTarget} onClose={() => setDeleteUserTarget(null)} onConfirm={handleDeleteUser} title="Delete Mailbox" message={`Delete "${deleteUserTarget?.username}@${domain.domain}"?`} impact="All mail data will be permanently lost." loading={deleteMutation.isPending} />
      <ConfirmDialog open={showDeleteDomain} onClose={() => setShowDeleteDomain(false)} onConfirm={handleDeleteDomain} title="Delete Domain" message={`Are you sure you want to delete "${domain.domain}"?`} impact={`Removes ${domain.domain} including mailboxes and DNS records.`} loading={deleteDomainMutation.isPending} />
      <ConfirmDialog
        open={showDkimConfirm}
        onClose={() => setShowDkimConfirm(false)}
        onConfirm={handleDkimRegenerate}
        title="Regenerate DKIM Key"
        message={`Generates a new DKIM key for ${domain.domain}.`}
        impact="DNS record must be updated; mail may fail DKIM checks until then."
        variant="warning"
        confirmLabel="Regenerate"
        loading={dkimMutation.isPending}
      />
      <ConfirmDialog
        open={showGroupwareConfirm}
        onClose={() => setShowGroupwareConfirm(false)}
        onConfirm={handleGroupwareToggle}
        title={domain.groupware_enabled ? 'Disable Groupware' : 'Enable Groupware'}
        message={domain.groupware_enabled ? `Disable SOGo groupware for ${domain.domain}?` : `Enable SOGo groupware for ${domain.domain}?`}
        impact={domain.groupware_enabled ? 'Users will lose access to calendars and contacts.' : 'SOGo CalDAV/CardDAV/ActiveSync will be available.'}
        variant="warning"
        confirmLabel={domain.groupware_enabled ? 'Disable' : 'Enable'}
        loading={enableGroupware.isPending || disableGroupware.isPending}
      />
    </div>
  )
}
