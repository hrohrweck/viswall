import { Link } from 'react-router-dom'
import { Plus, Shield, Network } from 'lucide-react'
import { useInstanceStore } from '../../stores/instance'
import { useVPNServers, useDeleteVPNServer } from '../../hooks/useApi'
import { InstanceSelector, StatusBadge, ProtocolBadge, EmptyState, LoadingSpinner, ConfirmDialog } from '../../components/ui'
import { useState } from 'react'
import type { VPNServer } from '../../types'
import { formatBytes } from '../../utils/format'

export function VPNServers() {
  const { selectedInstanceId } = useInstanceStore()
  const { data: servers, isLoading } = useVPNServers(selectedInstanceId!)
  const deleteMutation = useDeleteVPNServer(selectedInstanceId!)
  const [deleteTarget, setDeleteTarget] = useState<VPNServer | null>(null)

  const handleDelete = async () => {
    if (deleteTarget) {
      await deleteMutation.mutateAsync(deleteTarget.id)
      setDeleteTarget(null)
    }
  }

  if (!selectedInstanceId) {
    return (
      <div>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">VPN Servers</h2>
            <p className="text-gray-600 mt-1">Manage WireGuard, IPsec, OpenVPN, and legacy protocols</p>
          </div>
        </div>
        <EmptyState icon={Network} title="Select an Instance" description="Choose an instance to manage VPN servers." />
        <div className="mt-4"><InstanceSelector /></div>
      </div>
    )
  }

  if (isLoading) return <LoadingSpinner />

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">VPN Servers</h2>
            <p className="text-gray-600 mt-1">Manage WireGuard, IPsec, OpenVPN, and legacy protocols</p>
          </div>
          <InstanceSelector />
        </div>
        <Link
          to="/vpn/create"
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          <Plus className="w-5 h-5" />
          New VPN Server
        </Link>
      </div>

      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-lg mb-6 border border-blue-100">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-blue-100 rounded-lg">
            <Shield className="w-6 h-6 text-blue-700" />
          </div>
          <div>
            <h3 className="font-semibold text-blue-900">Recommended: WireGuard</h3>
            <p className="text-blue-800 text-sm mt-1">
              Modern, fast, and secure. WireGuard uses state-of-the-art cryptography
              and is recommended for all new deployments.
            </p>
          </div>
        </div>
      </div>

      {servers && servers.length > 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="divide-y divide-gray-200">
            {servers.map((server) => (
              <Link
                key={server.id}
                to={`/vpn/servers/${server.id}`}
                className="p-6 hover:bg-gray-50 flex items-center justify-between group"
              >
                <div className="flex items-center gap-4">
                  <ProtocolBadge protocol={server.protocol} />
                  <div>
                    <h3 className="font-semibold text-gray-900">{server.name}</h3>
                    <div className="flex items-center gap-3 text-sm text-gray-600 mt-1">
                      <span className="capitalize">{server.protocol}</span>
                      <span>•</span>
                      <span>Port {server.listen_port}</span>
                      <span>•</span>
                      <span>{server.network_cidr}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-6">
                  <span className="text-sm text-gray-600">
                    {server.connected_clients} connected
                  </span>
                  <span className="text-sm text-gray-600">
                    {formatBytes(server.bytes_received + server.bytes_sent)}
                  </span>
                  <StatusBadge status={server.status} />
                  <button
                    onClick={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      setDeleteTarget(server)
                    }}
                    className="text-sm text-red-600 hover:text-red-700 opacity-0 group-hover:opacity-100"
                  >
                    Delete
                  </button>
                </div>
              </Link>
            ))}
          </div>
        </div>
      ) : (
        <EmptyState
          icon={Network}
          title="No VPN servers"
          description="Create your first VPN server to enable remote access."
          actionLabel="Create VPN Server"
          actionTo="/vpn/create"
        />
      )}

      <ConfirmDialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Delete VPN Server"
        message={`Are you sure you want to delete "${deleteTarget?.name}"? All connected clients will be disconnected.`}
        loading={deleteMutation.isPending}
      />
    </div>
  )
}
