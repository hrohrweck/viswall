import { useParams, useNavigate, Link } from 'react-router-dom'
import { ArrowLeft, Copy, ExternalLink, Pencil, Trash2 } from 'lucide-react'
import { useInstance, useDeleteInstance, useUpdateInstance } from '../hooks/useApi'
import {
  PageHeader,
  Button,
  IconButton,
  Card,
  InstanceStatusBadge,
  ConfirmDialog,
  PageSkeleton,
  EmptyState,
  Modal,
  Field,
  Input,
  Textarea,
  toast,
} from '../components/ui'
import { useState } from 'react'
import { formatDistanceToNow } from 'date-fns'

export function InstanceDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const instanceId = Number(id)
  const { data: instance, isLoading } = useInstance(instanceId)
  const deleteMutation = useDeleteInstance()
  const updateMutation = useUpdateInstance()
  const [showDelete, setShowDelete] = useState(false)
  const [showEdit, setShowEdit] = useState(false)
  const [editName, setEditName] = useState('')
  const [editDescription, setEditDescription] = useState('')

  if (isLoading) return <PageSkeleton />
  if (!instance) return (
    <EmptyState
      icon={ExternalLink}
      title="Instance not found"
      description="The instance you are looking for does not exist or has been removed."
      actionLabel="Back to instances"
      actionTo="/instances"
    />
  )

  const copyToClipboard = async (text: string) => {
    await navigator.clipboard.writeText(text)
    toast.success('Copied')
  }

  const handleDelete = async () => {
    await deleteMutation.mutateAsync(instance.id)
    navigate('/instances')
  }

  const openEdit = () => {
    setEditName(instance.name)
    setEditDescription('')
    setShowEdit(true)
  }

  const handleEdit = async () => {
    await updateMutation.mutateAsync({ id: instance.id, name: editName })
    toast.success('Instance updated')
    setShowEdit(false)
  }

  return (
    <div className="space-y-6">
      <Link to="/instances" className="inline-flex items-center gap-1 text-sm text-on-surface-muted hover:text-on-surface transition-colors">
        <ArrowLeft className="w-4 h-4" />
        Back to instances
      </Link>

      <PageHeader
        title={instance.name}
        description={`${instance.hostname}`}
        primaryAction={
          <Button icon={Pencil} onClick={openEdit}>
            Edit
          </Button>
        }
        secondaryActions={[
          <Button key="delete" variant="destructive" icon={Trash2} onClick={() => setShowDelete(true)}>
            Delete
          </Button>,
        ]}
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Overview Card */}
        <Card title="Overview">
          <dl className="space-y-3">
            <div className="flex justify-between">
              <dt className="text-sm text-on-surface-muted">Status</dt>
              <dd><InstanceStatusBadge status={instance.status} /></dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-sm text-on-surface-muted">Last Seen</dt>
              <dd className="text-sm text-on-surface">
                {instance.last_seen
                  ? formatDistanceToNow(new Date(instance.last_seen), { addSuffix: true })
                  : 'Never'}
              </dd>
            </div>
            <div>
              <dt className="text-sm text-on-surface-muted mb-2">Capabilities</dt>
              <dd className="flex flex-wrap gap-2">
                {instance.capabilities.length > 0 ? (
                  instance.capabilities.map((cap) => (
                    <span
                      key={cap}
                      className="inline-flex items-center rounded-md bg-primary-subtle px-2.5 py-1 text-xs font-medium text-primary"
                    >
                      {cap}
                    </span>
                  ))
                ) : (
                  <span className="text-sm text-on-surface-muted">No capabilities assigned</span>
                )}
              </dd>
            </div>
          </dl>
        </Card>

        {/* Connection Card */}
        <Card title="Connection">
          <dl className="space-y-3">
            <div>
              <dt className="text-sm text-on-surface-muted mb-1">Hostname</dt>
              <dd className="flex items-center gap-2">
                <code className="font-mono text-sm bg-surface-elevated px-2 py-1 rounded flex-1 truncate text-on-surface">
                  {instance.hostname}
                </code>
                <IconButton icon={Copy} label="Copy hostname" onClick={() => copyToClipboard(instance.hostname)} />
              </dd>
            </div>
            <div>
              <dt className="text-sm text-on-surface-muted mb-1">API Endpoint</dt>
              <dd className="flex items-center gap-2">
                <code className="font-mono text-sm bg-surface-elevated px-2 py-1 rounded flex-1 truncate text-on-surface">
                  {instance.api_endpoint}
                </code>
                <IconButton icon={Copy} label="Copy API endpoint" onClick={() => copyToClipboard(instance.api_endpoint)} />
              </dd>
            </div>
          </dl>
        </Card>

        {/* Quick Links Card */}
        <Card title="Quick Links" className="lg:col-span-2">
          <div className="flex flex-wrap gap-3">
            <Link
              to={`/firewall?instance=${instance.id}`}
              className="inline-flex items-center gap-2 rounded-card border border-border bg-surface-card px-4 py-2 text-sm text-on-surface hover:bg-surface-elevated transition-colors"
            >
              <ExternalLink className="w-4 h-4" />
              Firewall Rules
            </Link>
            <Link
              to={`/vpn?instance=${instance.id}`}
              className="inline-flex items-center gap-2 rounded-card border border-border bg-surface-card px-4 py-2 text-sm text-on-surface hover:bg-surface-elevated transition-colors"
            >
              <ExternalLink className="w-4 h-4" />
              VPN Servers
            </Link>
            <Link
              to={`/mail?instance=${instance.id}`}
              className="inline-flex items-center gap-2 rounded-card border border-border bg-surface-card px-4 py-2 text-sm text-on-surface hover:bg-surface-elevated transition-colors"
            >
              <ExternalLink className="w-4 h-4" />
              Mail Domains
            </Link>
          </div>
        </Card>
      </div>

      {/* Edit Modal */}
      <Modal open={showEdit} onClose={() => setShowEdit(false)} title="Edit Instance">
        <div className="space-y-4">
          <Field label="Name">
            <Input
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              placeholder="Instance name"
            />
          </Field>
          <Field label="Description" helper="Optional description for this instance">
            <Textarea
              value={editDescription}
              onChange={(e) => setEditDescription(e.target.value)}
              placeholder="Optional description..."
            />
          </Field>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" onClick={() => setShowEdit(false)}>
              Cancel
            </Button>
            <Button onClick={handleEdit} loading={updateMutation.isPending} disabled={!editName.trim()}>
              Save
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete Confirm Dialog */}
      <ConfirmDialog
        open={showDelete}
        onClose={() => setShowDelete(false)}
        onConfirm={handleDelete}
        title="Delete Instance"
        message={`Are you sure you want to delete "${instance.name}"?`}
        impact={`Removes ${instance.name} and disconnects it from the manager.`}
        loading={deleteMutation.isPending}
      />
    </div>
  )
}
