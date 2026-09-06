import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Plus, Network, Info } from 'lucide-react'
import { useInstanceStore } from '../../stores/instance'
import { useVPNServers, useDeleteVPNServer } from '../../hooks/useApi'
import {
  VPNStatusBadge,
  ProtocolBadge,
  EmptyState,
  PageHeader,
  Card,
  DataTable,
  ConfirmDialog,
  QueryError,
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  buttonVariants,
  toast,
} from '../../components/ui'
import type { VPNServer } from '../../types'
import { formatBytes } from '../../utils/format'

export function VPNServers() {
  const { selectedInstanceId } = useInstanceStore()
  const navigate = useNavigate()
  const { data: servers, isLoading, isError, refetch } = useVPNServers(selectedInstanceId!)
  const deleteMutation = useDeleteVPNServer(selectedInstanceId!)
  const [deleteTarget, setDeleteTarget] = useState<VPNServer | null>(null)

  const handleDelete = async () => {
    if (!deleteTarget) return
    try {
      await deleteMutation.mutateAsync(deleteTarget.id)
      toast.success(`VPN server "${deleteTarget.name}" deleted`)
      setDeleteTarget(null)
    } catch {
      toast.error('Failed to delete VPN server')
    }
  }

  if (!selectedInstanceId) {
    return (
      <div>
        <PageHeader
          title="VPN Servers"
          description="WireGuard, IPsec and OpenVPN servers across your instances"
        />
        <Card className="mt-6">
          <div className="flex items-center gap-3 text-on-surface-muted">
            <Info className="h-5 w-5 shrink-0" />
            <p className="text-sm">Select an instance from the top bar to manage its VPN servers.</p>
          </div>
        </Card>
      </div>
    )
  }

  const columns = [
    {
      key: 'name',
      header: 'Server',
      render: (server: VPNServer) => (
        <div className="flex items-center gap-3">
          <ProtocolBadge protocol={server.protocol} />
          <div>
            <p className="font-medium text-on-surface">{server.name}</p>
            <p className="text-xs text-on-surface-muted capitalize">{server.protocol}</p>
          </div>
        </div>
      ),
    },
    {
      key: 'listen_port',
      header: 'Port',
      className: 'font-mono',
      render: (server: VPNServer) => (
        <span className="font-mono text-sm">{server.listen_port ?? '—'}</span>
      ),
    },
    {
      key: 'network_cidr',
      header: 'Tunnel network',
      className: 'font-mono',
      render: (server: VPNServer) => (
        <span className="font-mono text-sm">{server.network_cidr}</span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (server: VPNServer) => <VPNStatusBadge status={server.status} />,
    },
    {
      key: 'connected_clients',
      header: 'Clients',
      render: (server: VPNServer) => (
        <span className="text-sm">{server.connected_clients}</span>
      ),
    },
    {
      key: 'traffic',
      header: 'Traffic',
      render: (server: VPNServer) => (
        <span className="font-mono text-sm">
          ↑{formatBytes(server.bytes_sent)} ↓{formatBytes(server.bytes_received)}
        </span>
      ),
    },
  ]

  return (
    <div>
      <PageHeader
        title="VPN Servers"
        description="WireGuard, IPsec and OpenVPN servers across your instances"
        primaryAction={
          <Link to="/vpn/create" className={buttonVariants()}>
            <Plus className="w-4 h-4" />
            New VPN Server
          </Link>
        }
      />

      {isError ? (
        <QueryError onRetry={() => refetch()} />
      ) : (
        <DataTable
          columns={columns}
          data={servers ?? []}
          keyExtractor={(s) => s.id}
          isLoading={isLoading}
          onRowClick={(server) => navigate(`/vpn/servers/${server.id}`)}
          rowActions={(server) => (
            <DropdownMenu>
              <DropdownMenuTrigger />
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => navigate(`/vpn/servers/${server.id}`)}>
                  View
                </DropdownMenuItem>
                <DropdownMenuItem
                  danger
                  onClick={() => setDeleteTarget(server)}
                >
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
          emptyContent={
            <EmptyState
              icon={Network}
              title="No VPN servers"
              description="Create your first VPN server to enable remote access."
              actionLabel="Create VPN Server"
              actionTo="/vpn/create"
            />
          }
        />
      )}

      <ConfirmDialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Delete VPN Server"
        message={`Are you sure you want to delete "${deleteTarget?.name}"?`}
        impact={`Disconnects ${deleteTarget?.connected_clients ?? 0} connected clients.`}
        loading={deleteMutation.isPending}
      />
    </div>
  )
}
