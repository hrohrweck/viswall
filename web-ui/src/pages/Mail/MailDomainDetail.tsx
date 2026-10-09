import { useEffect, useMemo, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { Key, Trash2, Users, Brain, Globe, Forward } from 'lucide-react'
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
  useMailAliases,
  useCreateMailAlias,
  useUpdateMailAlias,
  useDeleteMailAlias,
  useUpdateMailDomain,
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
  Button,
  Field,
  Input,
} from '../../components/ui'
import { TabsContent } from '../../components/ui/Tabs'
import type { MailUser } from '../../types'
import { formatBytes } from '../../utils/format'
import { getErrMsg } from '../../lib/utils'
import { MailClassificationView } from './MailClassificationView'
import { MailboxForm } from '../../components/forms/MailboxForm'
import { MailAliasForm } from '../../components/forms/MailAliasForm'

interface AliasGroup {
  source: string
  destinations: string[]
  enabled: boolean
  aliasIds: number[]
}

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
  const { data: aliases } = useMailAliases(selectedInstanceId!, domainId)
  const createAliasMutation = useCreateMailAlias(selectedInstanceId!, domainId)
  const updateAliasMutation = useUpdateMailAlias(selectedInstanceId!, domainId)
  const deleteAliasMutation = useDeleteMailAlias(selectedInstanceId!, domainId)
  const updateDomainMutation = useUpdateMailDomain(selectedInstanceId!)

  const [showDeleteDomain, setShowDeleteDomain] = useState(false)
  const [showCreateUser, setShowCreateUser] = useState(false)
  const [deleteUserTarget, setDeleteUserTarget] = useState<MailUser | null>(null)
  const [showDkimConfirm, setShowDkimConfirm] = useState(false)
  const [showGroupwareConfirm, setShowGroupwareConfirm] = useState(false)
  const [showCreateAlias, setShowCreateAlias] = useState(false)
  const [editAliasTarget, setEditAliasTarget] = useState<AliasGroup | null>(null)
  const [deleteAliasTarget, setDeleteAliasTarget] = useState<AliasGroup | null>(null)
  const [activeTab, setActiveTab] = useState('users')
  const [mtaEnabled, setMtaEnabled] = useState(false)
  const [mtaHost, setMtaHost] = useState('')
  const [mtaPort, setMtaPort] = useState('25')
  const [mtaError, setMtaError] = useState<string | null>(null)

  useEffect(() => {
    if (domain) {
      setMtaEnabled(domain.mta_forward_enabled)
      setMtaHost(domain.mta_forward_host ?? '')
      setMtaPort(String(domain.mta_forward_port ?? 25))
    }
  }, [domain])

  const aliasGroups = useMemo<AliasGroup[]>(() => {
    const groups = new Map<string, AliasGroup>()
    for (const alias of aliases ?? []) {
      const group = groups.get(alias.source)
      if (group) {
        group.destinations.push(alias.destination)
        group.aliasIds.push(alias.id)
        group.enabled = group.enabled && alias.enabled
      } else {
        groups.set(alias.source, {
          source: alias.source,
          destinations: [alias.destination],
          enabled: alias.enabled,
          aliasIds: [alias.id],
        })
      }
    }
    return Array.from(groups.values())
  }, [aliases])

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
    try {
      await deleteDomainMutation.mutateAsync(domain.id)
      toast.success(`Domain "${domain.domain}" deleted`)
      navigate('/mail')
    } catch (e) {
      toast.error(getErrMsg(e))
    }
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

  const handleCreateAlias = async (values: { source: string; destinations: string[]; enabled: boolean }) => {
    try {
      await Promise.all(
        values.destinations.map((destination) =>
          createAliasMutation.mutateAsync({ source: values.source, destination, enabled: values.enabled }),
        ),
      )
      toast.success(`Alias "${values.source}" created`)
      setShowCreateAlias(false)
    } catch (e) {
      toast.error(getErrMsg(e))
    }
  }

  const handleEditAlias = async (values: { source: string; destinations: string[]; enabled: boolean }) => {
    if (!editAliasTarget) return
    const existing = editAliasTarget
    const added = values.destinations.filter((destination) => !existing.destinations.includes(destination))
    const removed = existing.aliasIds.filter(
      (id, index) => !values.destinations.includes(existing.destinations[index]),
    )
    const enabledChanged = values.enabled !== existing.enabled
    try {
      await Promise.all([
        ...added.map((destination) =>
          createAliasMutation.mutateAsync({ source: existing.source, destination, enabled: values.enabled }),
        ),
        ...removed.map((id) => deleteAliasMutation.mutateAsync(id)),
        ...(enabledChanged
          ? existing.aliasIds.map((id) => updateAliasMutation.mutateAsync({ id, enabled: values.enabled }))
          : []),
      ])
      toast.success(`Alias "${existing.source}" updated`)
      setEditAliasTarget(null)
    } catch (e) {
      toast.error(getErrMsg(e))
    }
  }

  const handleToggleAlias = async (group: AliasGroup) => {
    try {
      await Promise.all(group.aliasIds.map((id) => updateAliasMutation.mutateAsync({ id, enabled: !group.enabled })))
      toast.success(`Alias "${group.source}" ${group.enabled ? 'disabled' : 'enabled'}`)
    } catch (e) {
      toast.error(getErrMsg(e))
    }
  }

  const handleDeleteAlias = async () => {
    if (!deleteAliasTarget) return
    try {
      await Promise.all(deleteAliasTarget.aliasIds.map((id) => deleteAliasMutation.mutateAsync(id)))
      toast.success(`Alias "${deleteAliasTarget.source}" deleted`)
      setDeleteAliasTarget(null)
    } catch (e) {
      toast.error(getErrMsg(e))
    }
  }

  const handleMtaSave = async () => {
    const host = mtaHost.trim()
    if (mtaEnabled && !host) {
      setMtaError('A forwarding host is required')
      return
    }
    if (host && (/^[a-z][a-z0-9+.-]*:\/\//i.test(host) || /\s/.test(host))) {
      setMtaError('Invalid host — remove the scheme (http://) and spaces')
      return
    }
    setMtaError(null)
    const port = Number.parseInt(mtaPort, 10)
    try {
      await updateDomainMutation.mutateAsync({
        id: domain.id,
        mta_forward_enabled: mtaEnabled,
        mta_forward_host: host || null,
        mta_forward_port: Number.isInteger(port) && port > 0 ? port : 25,
      })
      toast.success('Delivery settings saved')
    } catch (e) {
      toast.error(getErrMsg(e))
    }
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

  const aliasColumns = [
    {
      key: 'source',
      header: 'Source',
      className: 'font-mono',
      render: (group: AliasGroup) => (
        <span className="font-medium text-on-surface">
          {group.source}@{domain.domain}
          {group.source === '*' && (
            <Badge variant="info" className="ml-2">Catch-all</Badge>
          )}
        </span>
      ),
    },
    {
      key: 'destinations',
      header: 'Destinations',
      render: (group: AliasGroup) => (
        <span className="text-sm text-on-surface-muted">{group.destinations.join(', ')}</span>
      ),
    },
    {
      key: 'enabled',
      header: 'Active',
      render: (group: AliasGroup) => (
        <Switch
          checked={group.enabled}
          onCheckedChange={() => handleToggleAlias(group)}
          aria-label={`Active: ${group.source}`}
        />
      ),
    },
  ]

  const tabItems = [
    { value: 'users', label: `Mailboxes (${users?.length ?? 0})` },
    { value: 'forwarding', label: `Forwarding (${aliasGroups.length})` },
    { value: 'delivery', label: 'Delivery' },
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

            <TabsContent value="forwarding">
              <div className="flex items-center justify-between mb-4 mt-4">
                <div>
                  <h3 className="text-lg font-semibold text-on-surface">Forwarding</h3>
                  <p className="text-sm text-on-surface-muted">
                    Forward mail from an address to one or more external destinations.
                  </p>
                </div>
                <button
                  onClick={() => setShowCreateAlias(true)}
                  className={buttonVariants({ size: 'sm' })}
                >
                  <Forward className="w-4 h-4" />
                  Add Alias
                </button>
              </div>
              <DataTable
                columns={aliasColumns}
                data={aliasGroups}
                keyExtractor={(group) => group.source}
                searchable
                searchPlaceholder="Search aliases…"
                rowActions={(group) => (
                  <DropdownMenu>
                    <DropdownMenuTrigger />
                    <DropdownMenuContent>
                      <DropdownMenuItem onClick={() => setEditAliasTarget(group)}>
                        Edit
                      </DropdownMenuItem>
                      <DropdownMenuItem danger onClick={() => setDeleteAliasTarget(group)}>
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                )}
                emptyContent={<EmptyState icon={Forward} title="No forwarding rules yet" description="Forward mail for an address — or your whole domain — to external mailboxes." actionLabel="Add Alias" onAction={() => setShowCreateAlias(true)} />}
              />
            </TabsContent>

            <TabsContent value="delivery">
              <div className="mt-4">
                <Card>
                  <div className="space-y-6">
                    <div className="flex items-start justify-between gap-6">
                      <div className="space-y-1">
                        <p className="text-sm font-medium text-on-surface">
                          Forward all incoming mail via SMTP (MTA forwarding)
                        </p>
                        <p className="text-sm text-on-surface-muted">
                          Relay every message arriving for {domain.domain} to an external SMTP server instead of delivering locally.
                        </p>
                      </div>
                      <Switch
                        checked={mtaEnabled}
                        onCheckedChange={(checked) => {
                          setMtaEnabled(checked)
                          setMtaError(null)
                        }}
                        aria-label="MTA forwarding"
                      />
                    </div>

                    <div className="grid gap-4 md:grid-cols-[1fr_9rem]">
                      <Field
                        label="Forwarding host"
                        required={mtaEnabled}
                        error={mtaError ?? undefined}
                        helper="Hostname or IP address of the external SMTP server"
                      >
                        <Input
                          aria-label="Forwarding host"
                          placeholder="e.g. 83.164.137.172 or mail.example.com"
                          value={mtaHost}
                          onChange={(e) => setMtaHost(e.target.value)}
                          disabled={!mtaEnabled}
                        />
                      </Field>
                      <Field label="Port" helper="SMTP port (default 25)">
                        <Input
                          aria-label="Forwarding port"
                          type="number"
                          value={mtaPort}
                          onChange={(e) => setMtaPort(e.target.value)}
                          disabled={!mtaEnabled}
                        />
                      </Field>
                    </div>

                    <div className="flex justify-end gap-3">
                      <Button onClick={handleMtaSave} disabled={updateDomainMutation.isPending}>
                        {updateDomainMutation.isPending ? 'Saving…' : 'Save'}
                      </Button>
                    </div>
                  </div>
                </Card>
              </div>
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

      <Modal open={showCreateAlias} onClose={() => setShowCreateAlias(false)} title="Add Alias">
        <MailAliasForm
          domain={domain.domain}
          mode="create"
          loading={createAliasMutation.isPending}
          onSubmit={handleCreateAlias}
          onCancel={() => setShowCreateAlias(false)}
        />
      </Modal>

      <Modal open={!!editAliasTarget} onClose={() => setEditAliasTarget(null)} title="Edit Alias">
        {editAliasTarget && (
          <MailAliasForm
            domain={domain.domain}
            mode="edit"
            initial={{
              source: editAliasTarget.source,
              destinations: editAliasTarget.destinations,
              enabled: editAliasTarget.enabled,
            }}
            loading={createAliasMutation.isPending || updateAliasMutation.isPending || deleteAliasMutation.isPending}
            onSubmit={handleEditAlias}
            onCancel={() => setEditAliasTarget(null)}
          />
        )}
      </Modal>

      <ConfirmDialog open={!!deleteUserTarget} onClose={() => setDeleteUserTarget(null)} onConfirm={handleDeleteUser} title="Delete Mailbox" message={`Delete "${deleteUserTarget?.username}@${domain.domain}"?`} impact="All mail data will be permanently lost." loading={deleteMutation.isPending} />
      <ConfirmDialog
        open={!!deleteAliasTarget}
        onClose={() => setDeleteAliasTarget(null)}
        onConfirm={handleDeleteAlias}
        title="Delete Alias"
        message={`Delete "${deleteAliasTarget?.source}@${domain.domain}"?`}
        impact={deleteAliasTarget ? `Mail to ${deleteAliasTarget.source}@${domain.domain} will no longer be forwarded to ${deleteAliasTarget.destinations.join(', ')}.` : ''}
        loading={deleteAliasMutation.isPending}
      />
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
