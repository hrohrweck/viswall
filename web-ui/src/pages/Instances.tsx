import { useState } from 'react'
import { Plus, Eye, Pencil, Trash2 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useInstances, useCreateInstance, useDeleteInstance } from '../hooks/useApi'
import {
  PageHeader,
  Button,
  DataTable,
  InstanceStatusBadge,
  Modal,
  ConfirmDialog,
  EmptyState,
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  toast,
} from '../components/ui'
import type { Instance, InstanceCreate } from '../types'
import { formatDistanceToNow } from 'date-fns'
import { InstanceCreateForm } from '../components/forms/InstanceCreateForm'

export function Instances() {
  const { data: instances, isLoading, isError, refetch } = useInstances()
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
      toast.success('Instance deleted')
      setDeleteTarget(null)
    }
  }

  const columns = [
    {
      key: 'name',
      header: 'Instance',
      render: (item: Instance) => (
        <div>
          <p className="font-medium text-on-surface">{item.name}</p>
          <p className="font-mono text-xs text-on-surface-muted">{item.hostname}</p>
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (item: Instance) => <InstanceStatusBadge status={item.status} />,
    },
    {
      key: 'capabilities',
      header: 'Capabilities',
      render: (item: Instance) => (
        <div className="flex flex-wrap gap-1">
          {item.capabilities.length > 0
            ? item.capabilities.map((c) => (
                <span key={c} className="inline-flex items-center rounded-md bg-surface-elevated px-2 py-0.5 text-xs font-medium text-on-surface-muted">
                  {c}
                </span>
              ))
            : <span className="text-xs text-on-surface-muted">None</span>}
        </div>
      ),
    },
    {
      key: 'last_seen',
      header: 'Last seen',
      render: (item: Instance) => (
        <span className="text-sm text-on-surface-muted">
          {item.last_seen
            ? formatDistanceToNow(new Date(item.last_seen), { addSuffix: true })
            : 'Never'}
        </span>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title="Instances"
        description="Manage your viswall instances and their configurations."
        primaryAction={
          <Button icon={Plus} onClick={() => setShowCreate(true)}>
            Add instance
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={instances || []}
        keyExtractor={(item) => item.id}
        enableSorting
        searchable
        searchPlaceholder="Search instances..."
        pagination
        isLoading={isLoading}
        isError={isError}
        onRetry={() => refetch()}
        onRowClick={(item) => navigate(`/instances/${item.id}`)}
        rowActions={(item) => (
          <DropdownMenu>
            <DropdownMenuTrigger label="Instance actions" />
            <DropdownMenuContent>
              <DropdownMenuItem onClick={() => navigate(`/instances/${item.id}`)}>
                <Eye className="mr-2 h-4 w-4" />
                View
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => navigate(`/instances/${item.id}`)}>
                <Pencil className="mr-2 h-4 w-4" />
                Edit instance
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                danger
                onClick={(e) => {
                  e.stopPropagation()
                  setDeleteTarget(item)
                }}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
        emptyContent={
          <EmptyState
            icon={Plus}
            title="No instances yet"
            description="Add your first viswall instance to get started."
            actionLabel="Add instance"
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
        message={`Are you sure you want to delete "${deleteTarget?.name}"?`}
        impact={deleteTarget ? `Removes ${deleteTarget.name} and disconnects it from the manager.` : undefined}
        loading={deleteMutation.isPending}
      />
    </div>
  )
}
