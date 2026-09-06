import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { Users, Activity, Clock, ArrowLeft, RotateCcw, Square, Plus, Trash2, Copy } from 'lucide-react'
import { useInstanceStore } from '../../stores/instance'
import {
  useVPNServer,
  useVPNClients,
  useDeleteVPNServer,
  useVPNServerAction,
  useCreateVPNClient,
  useDeleteVPNClient,
} from '../../hooks/useApi'
import {
  StatusBadge,
  VPNStatusBadge,
  ProtocolBadge,
  ConfirmDialog,
  EmptyState,
  PageHeader,
  DataTable,
  Card,
  CardBody,
  Modal,
  Field,
  Input,
  Button,
  IconButton,
  Skeleton,
  SkeletonText,
  QueryError,
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  toast,
  Tabs,
} from '../../components/ui'
import { TabsContent } from '../../components/ui/Tabs'
import type { VPNClient } from '../../types'
import { formatBytes } from '../../utils/format'
import { getErrMsg } from '../../lib/utils'

function relativeTime(iso: string | null): string {
  if (!iso) return 'Never'
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60_000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  return `${days}d ago`
}

function uptimeSince(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const hrs = Math.floor(diff / 3_600_000)
  if (hrs < 24) return `${hrs}h`
  const days = Math.floor(hrs / 24)
  return `${days}d ${hrs % 24}h`
}

export function VPNServerDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { selectedInstanceId } = useInstanceStore()
  const serverId = Number(id)

  const { data: server, isLoading, isError, refetch } = useVPNServer(selectedInstanceId!, serverId)
  const { data: clients } = useVPNClients(selectedInstanceId!, serverId)
  const deleteServerMutation = useDeleteVPNServer(selectedInstanceId!)
  const actionMutation = useVPNServerAction(selectedInstanceId!)
  const createClientMutation = useCreateVPNClient(selectedInstanceId!, serverId)
  const deleteClientMutation = useDeleteVPNClient(selectedInstanceId!, serverId)

  const [showDeleteServer, setShowDeleteServer] = useState(false)
  const [showStopServer, setShowStopServer] = useState(false)
  const [showCreateClient, setShowCreateClient] = useState(false)
  const [deleteClientTarget, setDeleteClientTarget] = useState<VPNClient | null>(null)
  const [newClientName, setNewClientName] = useState('')
  const [newClientIp, setNewClientIp] = useState('')
  const [clientNameError, setClientNameError] = useState('')

  /* ── Loading / error / not-found ── */
  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-72" />
        <div className="grid grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-28 rounded-card" />
          ))}
        </div>
        <SkeletonText lines={5} />
      </div>
    )
  }

  if (!server) {
    return (
      <EmptyState
        icon={Users}
        title="VPN server not found"
        description="The server you're looking for doesn't exist or has been deleted."
        actionLabel="Back to VPN Servers"
        actionTo="/vpn"
      />
    )
  }

  /* ── Handlers ── */
  const handleStop = async () => {
    try {
      await actionMutation.mutateAsync({ serverId, action: 'stop' })
      toast.success(`VPN server "${server.name}" stopped`)
    } catch (e) {
      toast.error(getErrMsg(e))
    }
    setShowStopServer(false)
  }

  const handleRestart = async () => {
    try {
      await actionMutation.mutateAsync({ serverId, action: 'restart' })
      toast.success(`VPN server "${server.name}" restarted`)
    } catch (e) {
      toast.error(getErrMsg(e))
    }
  }

  const handleDeleteServer = async () => {
    try {
      await deleteServerMutation.mutateAsync(server.id)
      toast.success(`VPN server "${server.name}" deleted`)
      navigate('/vpn')
    } catch (e) {
      toast.error(getErrMsg(e))
    }
  }

  const handleCreateClient = async () => {
    if (!newClientName.trim()) {
      setClientNameError('Client name is required')
      return
    }
    setClientNameError('')
    try {
      await createClientMutation.mutateAsync({
        name: newClientName.trim(),
        ...(newClientIp.trim() ? { assigned_ip: newClientIp.trim() } : {}),
      })
      toast.success(`Client "${newClientName}" created`)
      setNewClientName('')
      setNewClientIp('')
      setShowCreateClient(false)
    } catch (e) {
      toast.error(getErrMsg(e))
    }
  }

  const handleDeleteClient = async () => {
    if (!deleteClientTarget) return
    try {
      await deleteClientMutation.mutateAsync(deleteClientTarget.id)
      toast.success(`Client "${deleteClientTarget.name}" revoked`)
      setDeleteClientTarget(null)
    } catch (e) {
      toast.error(getErrMsg(e))
    }
  }

  /* ── Description mono line ── */
  const descParts = [
    `udp/${String(server.listen_port ?? '—')}`,
    server.network_cidr,
    server.ipv6_tunnel_network,
  ].filter(Boolean)

  /* ── Client table columns ── */
  const clientColumns = [
    {
      key: 'name',
      header: 'Client',
      render: (client: VPNClient) => (
        <div>
          <p className="font-medium text-on-surface">{client.name}</p>
          {client.assigned_ip && (
            <p className="text-xs text-on-surface-muted">{client.assigned_ip}</p>
          )}
        </div>
      ),
    },
    {
      key: 'assigned_ip',
      header: 'Address',
      render: (client: VPNClient) => (
        <span className="font-mono text-sm">{client.assigned_ip ?? '—'}</span>
      ),
    },
    {
      key: 'public_key',
      header: 'Public key',
      render: (client: VPNClient) => {
        const key = client.public_key
        if (!key) return <span className="text-on-surface-muted">—</span>
        const truncated = key.length > 20 ? `${key.slice(0, 12)}…${key.slice(-6)}` : key
        return (
          <span className="flex items-center gap-1">
            <span className="font-mono text-sm truncate max-w-[140px]" title={key}>
              {truncated}
            </span>
            <IconButton
              icon={Copy}
              label="Copy public key"
              size="sm"
              variant="ghost"
              onClick={() => {
                void navigator.clipboard.writeText(key)
                toast.success('Public key copied')
              }}
            />
          </span>
        )
      },
    },
    {
      key: 'last_connected',
      header: 'Last handshake',
      render: (client: VPNClient) => (
        <span className="text-sm text-on-surface-muted">{relativeTime(client.last_connected)}</span>
      ),
    },
    {
      key: 'transfer',
      header: 'Transfer',
      render: (client: VPNClient) => (
        <span className="font-mono text-sm">
          ↑{formatBytes(client.bytes_sent)} ↓{formatBytes(client.bytes_received)}
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (client: VPNClient) => (
        <StatusBadge status={client.enabled ? 'active' : 'inactive'} />
      ),
    },
  ]

  /* ── Render ── */
  return (
    <div>
      <Link to="/vpn" className="inline-flex items-center gap-1 text-sm text-on-surface-muted hover:text-on-surface mb-4">
        <ArrowLeft className="w-4 h-4" />
        Back to VPN Servers
      </Link>

      <PageHeader
        title={server.name}
        description={descParts.join(' · ')}
        secondaryActions={[
          <Button
            key="restart"
            variant="secondary"
            icon={RotateCcw}
            onClick={handleRestart}
            loading={actionMutation.isPending}
          >
            Restart
          </Button>,
          <Button
            key="stop"
            variant="secondary"
            icon={Square}
            onClick={() => setShowStopServer(true)}
          >
            Stop
          </Button>,
        ]}
        primaryAction={
          <DropdownMenu>
            <DropdownMenuTrigger />
            <DropdownMenuContent>
              <DropdownMenuItem danger onClick={() => setShowDeleteServer(true)}>
                <Trash2 className="w-4 h-4 mr-2" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        }
      />

      {/* Badges row under title */}
      <div className="flex items-center gap-2 mt-2 mb-6">
        <ProtocolBadge protocol={server.protocol} />
        <VPNStatusBadge status={server.status} />
      </div>

      {/* ── Stat cards ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <Card>
          <CardBody>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary-subtle rounded-card">
                <Users className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="text-sm text-on-surface-muted">Connected clients</p>
                <p className="text-2xl font-semibold text-on-surface">
                  {server.connected_clients}
                  <span className="text-sm font-normal text-on-surface-muted">
                    /{clients?.length ?? 0}
                  </span>
                </p>
              </div>
            </div>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-success-subtle rounded-card">
                <Activity className="w-5 h-5 text-success" />
              </div>
              <div>
                <p className="text-sm text-on-surface-muted">Traffic today</p>
                <p className="font-mono text-2xl font-semibold text-on-surface">
                  ↑{formatBytes(server.bytes_sent)} ↓{formatBytes(server.bytes_received)}
                </p>
              </div>
            </div>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-info-subtle rounded-card">
                <Clock className="w-5 h-5 text-info" />
              </div>
              <div>
                <p className="text-sm text-on-surface-muted">Uptime</p>
                <p className="text-2xl font-semibold text-on-surface">
                  {uptimeSince(server.created_at)}
                </p>
              </div>
            </div>
          </CardBody>
        </Card>
      </div>

      {/* ── Tabs: Clients / Configuration ── */}
      <Tabs
        items={[
          { value: 'clients', label: 'Clients' },
          { value: 'config', label: 'Configuration' },
        ]}
        defaultValue="clients"
      >
        <TabsContent value="clients">
          <div className="flex items-center justify-between mb-4">
            <div />
            <Button icon={Plus} onClick={() => setShowCreateClient(true)}>
              Add Client
            </Button>
          </div>
          <DataTable
            columns={clientColumns}
            data={clients ?? []}
            keyExtractor={(c) => c.id}
            searchable
            searchPlaceholder="Search clients…"
            rowActions={(client) => (
              <DropdownMenu>
                <DropdownMenuTrigger />
                <DropdownMenuContent>
                  <DropdownMenuItem onClick={() => setDeleteClientTarget(client)}>
                    Revoke
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            )}
            emptyContent={
              <EmptyState
                icon={Users}
                title="No clients"
                description="Add a client to connect to this VPN server."
                actionLabel="Add Client"
                onAction={() => setShowCreateClient(true)}
              />
            }
          />
        </TabsContent>
        <TabsContent value="config">
          <Card>
            <CardBody>
              <dl className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <dt className="text-on-surface-muted">Protocol</dt>
                  <dd className="font-medium capitalize">{server.protocol}</dd>
                </div>
                <div>
                  <dt className="text-on-surface-muted">Listen address</dt>
                  <dd className="font-mono">{server.listen_address}:{server.listen_port}</dd>
                </div>
                <div>
                  <dt className="text-on-surface-muted">Tunnel network</dt>
                  <dd className="font-mono">{server.network_cidr}</dd>
                </div>
                {server.ipv6_tunnel_network && (
                  <div>
                    <dt className="text-on-surface-muted">IPv6 tunnel</dt>
                    <dd className="font-mono">{server.ipv6_tunnel_network}</dd>
                  </div>
                )}
                <div>
                  <dt className="text-on-surface-muted">DNS servers</dt>
                  <dd className="font-mono">{server.dns_servers.join(', ')}</dd>
                </div>
                <div>
                  <dt className="text-on-surface-muted">Internet redirect</dt>
                  <dd>{server.internet_redirect ? 'Yes' : 'No'}</dd>
                </div>
              </dl>
            </CardBody>
          </Card>
        </TabsContent>
      </Tabs>

      {/* ── Add client modal ── */}
      <Modal open={showCreateClient} onClose={() => setShowCreateClient(false)} title="Add VPN Client">
        <div className="space-y-4">
          <Field label="Client Name" error={clientNameError}>
            <Input
              value={newClientName}
              onChange={(e) => {
                setNewClientName(e.target.value)
                if (clientNameError) setClientNameError('')
              }}
              placeholder="e.g. John's Laptop"
            />
          </Field>
          <Field label="Assigned IP (optional)" helper="Leave empty for auto-assignment">
            <Input
              mono
              value={newClientIp}
              onChange={(e) => setNewClientIp(e.target.value)}
              placeholder="10.10.0.5"
            />
          </Field>
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setShowCreateClient(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateClient} loading={createClientMutation.isPending}>
              Create
            </Button>
          </div>
        </div>
      </Modal>

      {/* ── Stop confirm ── */}
      <ConfirmDialog
        open={showStopServer}
        onClose={() => setShowStopServer(false)}
        onConfirm={handleStop}
        title="Stop VPN Server"
        message={`Stop "${server.name}"?`}
        impact={`Disconnects ${clients?.length ?? 0} connected clients.`}
        confirmLabel="Stop"
        variant="warning"
        loading={actionMutation.isPending}
      />

      {/* ── Delete server confirm ── */}
      <ConfirmDialog
        open={showDeleteServer}
        onClose={() => setShowDeleteServer(false)}
        onConfirm={handleDeleteServer}
        title="Delete VPN Server"
        message={`Delete "${server.name}"? This cannot be undone.`}
        impact={`Disconnects ${clients?.length ?? 0} connected clients and removes all configuration.`}
        loading={deleteServerMutation.isPending}
      />

      {/* ── Revoke client confirm ── */}
      <ConfirmDialog
        open={!!deleteClientTarget}
        onClose={() => setDeleteClientTarget(null)}
        onConfirm={handleDeleteClient}
        title="Revoke Client"
        message={`Revoke access for "${deleteClientTarget?.name}"?`}
        impact="The client will lose access immediately and cannot reconnect."
        confirmLabel="Revoke"
        loading={deleteClientMutation.isPending}
      />
    </div>
  )
}
