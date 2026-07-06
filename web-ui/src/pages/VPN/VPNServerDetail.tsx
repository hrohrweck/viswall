import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Users, Activity, Play, Square, RotateCcw, Plus, Trash2 } from 'lucide-react'
import { useInstanceStore } from '../../stores/instance'
import {
  useVPNServer,
  useVPNClients,
  useDeleteVPNServer,
  useVPNServerAction,
  useCreateVPNClient,
  useDeleteVPNClient,
} from '../../hooks/useApi'
import { StatusBadge, ProtocolBadge, Modal, ConfirmDialog, LoadingSpinner, EmptyState, DataTable } from '../../components/ui'
import type { VPNClient } from '../../types'
import { formatBytes } from '../../utils/format'

export function VPNServerDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { selectedInstanceId } = useInstanceStore()
  const serverId = Number(id)
  const { data: server, isLoading } = useVPNServer(selectedInstanceId!, serverId)
  const { data: clients } = useVPNClients(selectedInstanceId!, serverId)
  const deleteServerMutation = useDeleteVPNServer(selectedInstanceId!)
  const actionMutation = useVPNServerAction(selectedInstanceId!)
  const createClientMutation = useCreateVPNClient(selectedInstanceId!, serverId)
  const deleteClientMutation = useDeleteVPNClient(selectedInstanceId!, serverId)

  const [showDeleteServer, setShowDeleteServer] = useState(false)
  const [showCreateClient, setShowCreateClient] = useState(false)
  const [deleteClientTarget, setDeleteClientTarget] = useState<VPNClient | null>(null)
  const [newClientName, setNewClientName] = useState('')

  if (isLoading) return <LoadingSpinner />
  if (!server) return <p className="text-gray-600">Server not found.</p>

  const handleAction = (action: 'start' | 'stop' | 'restart') => {
    actionMutation.mutate({ serverId, action })
  }

  const handleCreateClient = async () => {
    await createClientMutation.mutateAsync({ name: newClientName })
    setNewClientName('')
    setShowCreateClient(false)
  }

  const handleDeleteServer = async () => {
    await deleteServerMutation.mutateAsync(server.id)
    navigate('/vpn')
  }

  const handleDeleteClient = async () => {
    if (deleteClientTarget) {
      await deleteClientMutation.mutateAsync(deleteClientTarget.id)
      setDeleteClientTarget(null)
    }
  }

  const clientColumns = [
    {
      key: 'name',
      header: 'Client',
      render: (client: VPNClient) => (
        <div>
          <p className="font-medium text-gray-900 dark:text-white">{client.name}</p>
          {client.assigned_ip && <p className="text-xs text-gray-500 dark:text-gray-400">IP: {client.assigned_ip}</p>}
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (client: VPNClient) => <StatusBadge status={client.enabled ? 'active' : 'inactive'} />,
    },
    {
      key: 'connections',
      header: 'Connections',
      render: (client: VPNClient) => <span className="text-sm text-gray-600 dark:text-gray-400">{client.connection_count}</span>,
    },
    {
      key: 'traffic',
      header: 'Traffic',
      render: (client: VPNClient) => (
        <span className="text-sm text-gray-600 dark:text-gray-400">{formatBytes(client.bytes_received + client.bytes_sent)}</span>
      ),
    },
    {
      key: 'actions',
      header: '',
      render: (client: VPNClient) => (
        <button
          onClick={(e) => { e.stopPropagation(); setDeleteClientTarget(client) }}
          className="text-sm text-red-600 hover:text-red-700"
        >
          Revoke
        </button>
      ),
    },
  ]

  return (
    <div>
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate('/vpn')} className="p-2 hover:bg-gray-100 rounded-lg dark:hover:bg-gray-800">
          <ArrowLeft className="w-5 h-5 text-gray-600 dark:text-gray-400" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">{server.name}</h2>
            <ProtocolBadge protocol={server.protocol} />
            <StatusBadge status={server.status} />
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {server.listen_address}:{server.listen_port} | {server.network_cidr}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => handleAction('start')} disabled={actionMutation.isPending} className="p-2 text-green-600 hover:bg-green-50 rounded-lg dark:hover:bg-gray-800" title="Start">
            <Play className="w-5 h-5" />
          </button>
          <button onClick={() => handleAction('stop')} disabled={actionMutation.isPending} className="p-2 text-red-600 hover:bg-red-50 rounded-lg dark:hover:bg-gray-800" title="Stop">
            <Square className="w-5 h-5" />
          </button>
          <button onClick={() => handleAction('restart')} disabled={actionMutation.isPending} className="p-2 text-yellow-600 hover:bg-yellow-50 rounded-lg dark:hover:bg-gray-800" title="Restart">
            <RotateCcw className="w-5 h-5" />
          </button>
          <button onClick={() => setShowDeleteServer(true)} className="p-2 text-red-600 hover:bg-red-50 rounded-lg dark:hover:bg-gray-800" title="Delete">
            <Trash2 className="w-5 h-5" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 dark:bg-gray-900 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <Users className="w-5 h-5 text-primary-600" />
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Connected Clients</p>
              <p className="text-2xl font-bold dark:text-white">{server.connected_clients}</p>
            </div>
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 dark:bg-gray-900 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <Activity className="w-5 h-5 text-green-600" />
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Total Traffic</p>
              <p className="text-2xl font-bold dark:text-white">{formatBytes(server.bytes_received + server.bytes_sent)}</p>
            </div>
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 dark:bg-gray-900 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <Activity className="w-5 h-5 text-indigo-600" />
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">DNS Servers</p>
              <p className="text-sm font-medium dark:text-white">{server.dns_servers.join(', ')}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Clients</h3>
        <button
          onClick={() => setShowCreateClient(true)}
          className="flex items-center gap-2 px-3 py-1.5 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm"
        >
          <Plus className="w-4 h-4" />
          Add Client
        </button>
      </div>

      <DataTable
        columns={clientColumns}
        data={clients || []}
        keyExtractor={(c) => c.id}
        emptyContent={<EmptyState icon={Users} title="No clients" description="Add a client to connect to this VPN server." actionLabel="Add Client" onAction={() => setShowCreateClient(true)} />}
      />

      <Modal open={showCreateClient} onClose={() => setShowCreateClient(false)} title="Add VPN Client">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">Client Name</label>
            <input
              type="text"
              value={newClientName}
              onChange={(e) => setNewClientName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
              placeholder="e.g. John's Laptop"
            />
          </div>
          <div className="flex justify-end gap-3">
            <button onClick={() => setShowCreateClient(false)} className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 dark:bg-gray-700 dark:text-white dark:hover:bg-gray-600">Cancel</button>
            <button onClick={handleCreateClient} disabled={!newClientName || createClientMutation.isPending} className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50">
              {createClientMutation.isPending ? 'Creating...' : 'Create'}
            </button>
          </div>
        </div>
      </Modal>

      <ConfirmDialog open={!!deleteClientTarget} onClose={() => setDeleteClientTarget(null)} onConfirm={handleDeleteClient} title="Revoke Client" message={`Revoke access for "${deleteClientTarget?.name}"?`} loading={deleteClientMutation.isPending} confirmLabel="Revoke" />
      <ConfirmDialog open={showDeleteServer} onClose={() => setShowDeleteServer(false)} onConfirm={handleDeleteServer} title="Delete VPN Server" message={`Delete "${server.name}"? All clients will be permanently removed.`} loading={deleteServerMutation.isPending} />
    </div>
  )
}
