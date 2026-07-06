import { useState } from 'react'
import { Plus } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useInstances, useCreateInstance, useDeleteInstance } from '../hooks/useApi'
import { DataTable, StatusBadge, Modal, ConfirmDialog, LoadingSpinner, EmptyState } from '../components/ui'
import type { Instance, InstanceCreate } from '../types'
import { formatDistanceToNow } from 'date-fns'
import { InstanceCreateForm } from '../components/forms/InstanceCreateForm'

export function Instances() {
  const { data: instances, isLoading } = useInstances()
  const createMutation = useCreateInstance()
  const deleteMutation = useDeleteInstance()
  const navigate = useNavigate()
  const [showCreate, setShowCreate] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<Instance | null>(null)

  const handleCreate = async (data: InstanceCreate) => {
    const instance = await createMutation.mutateAsync(data)
    setShowCreate(false)
    navigate(`/instances/${instance.id}`)
  }

  const handleDelete = async () => {
    if (deleteTarget) {
      await deleteMutation.mutateAsync(deleteTarget.id)
      setDeleteTarget(null)
    }
  }

  if (isLoading) return <LoadingSpinner />

  const columns = [
    {
      key: 'name',
      header: 'Name',
      render: (item: Instance) => (
        <div>
          <p className="font-medium text-gray-900 dark:text-white">{item.name}</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">{item.hostname}</p>
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (item: Instance) => <StatusBadge status={item.status} />,
    },
    {
      key: 'capabilities',
      header: 'Capabilities',
      render: (item: Instance) => (
        <div className="flex flex-wrap gap-1">
          {item.capabilities.length > 0
            ? item.capabilities.map((c) => (
                <span key={c} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs dark:bg-gray-800 dark:text-gray-300">
                  {c}
                </span>
              ))
            : <span className="text-gray-400 text-xs dark:text-gray-500">None</span>}
        </div>
      ),
    },
    {
      key: 'last_seen',
      header: 'Last Seen',
      render: (item: Instance) => (
        <span className="text-sm text-gray-500 dark:text-gray-400">
          {item.last_seen
            ? formatDistanceToNow(new Date(item.last_seen), { addSuffix: true })
            : 'Never'}
        </span>
      ),
    },
    {
      key: 'actions',
      header: '',
      render: (item: Instance) => (
        <button
          onClick={(e) => {
            e.stopPropagation()
            setDeleteTarget(item)
          }}
          className="text-sm text-red-600 hover:text-red-700"
        >
          Delete
        </button>
      ),
    },
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Instances</h2>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          <Plus className="w-5 h-5" />
          Add Instance
        </button>
      </div>

      <DataTable
        columns={columns}
        data={instances || []}
        keyExtractor={(item) => item.id}
        onRowClick={(item) => navigate(`/instances/${item.id}`)}
        emptyContent={
          <EmptyState
            icon={Plus}
            title="No instances yet"
            description="Add your first viswall instance to get started."
            actionLabel="Add Instance"
            onAction={() => setShowCreate(true)}
          />
        }
      />

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Add Instance">
        <InstanceCreateForm
          onSubmit={handleCreate}
          onCancel={() => setShowCreate(false)}
          loading={createMutation.isPending}
        />
      </Modal>

      <ConfirmDialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Delete Instance"
        message={`Are you sure you want to delete "${deleteTarget?.name}"? This action cannot be undone.`}
        loading={deleteMutation.isPending}
      />
    </div>
  )
}
