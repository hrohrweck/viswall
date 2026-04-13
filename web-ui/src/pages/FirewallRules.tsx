import { useState } from 'react'
import { Plus, Shield, ArrowUp, ArrowDown, Upload } from 'lucide-react'
import { useInstanceStore } from '../stores/instance'
import {
  useFirewallRules,
  useCreateFirewallRule,
  useUpdateFirewallRule,
  useDeleteFirewallRule,
  useReorderFirewallRule,
  useDeployFirewall,
} from '../hooks/useApi'
import {
  InstanceSelector,
  DataTable,
  Modal,
  ConfirmDialog,
  EmptyState,
  LoadingSpinner,
} from '../components/ui'
import { FirewallRuleForm } from '../components/forms/FirewallRuleForm'
import type { FirewallRule, FirewallRuleCreate, FirewallRuleUpdate } from '../types'

export function FirewallRules() {
  const { selectedInstanceId } = useInstanceStore()
  const { data: rules, isLoading } = useFirewallRules(selectedInstanceId!)
  const createMutation = useCreateFirewallRule(selectedInstanceId!)
  const updateMutation = useUpdateFirewallRule(selectedInstanceId!)
  const deleteMutation = useDeleteFirewallRule(selectedInstanceId!)
  const reorderMutation = useReorderFirewallRule(selectedInstanceId!)
  const deployMutation = useDeployFirewall(selectedInstanceId!)

  const [showCreate, setShowCreate] = useState(false)
  const [editTarget, setEditTarget] = useState<FirewallRule | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<FirewallRule | null>(null)

  const handleCreate = async (data: FirewallRuleCreate | FirewallRuleUpdate) => {
    await createMutation.mutateAsync(data as FirewallRuleCreate)
    setShowCreate(false)
  }

  const handleUpdate = async (data: FirewallRuleUpdate) => {
    if (editTarget) {
      await updateMutation.mutateAsync({ id: editTarget.id, ...data })
      setEditTarget(null)
    }
  }

  const handleDelete = async () => {
    if (deleteTarget) {
      await deleteMutation.mutateAsync(deleteTarget.id)
      setDeleteTarget(null)
    }
  }

  if (!selectedInstanceId) {
    return (
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Firewall Rules</h2>
        <EmptyState
          icon={Shield}
          title="Select an Instance"
          description="Choose an instance from the dropdown above to manage its firewall rules."
        />
        <div className="mt-4">
          <InstanceSelector />
        </div>
      </div>
    )
  }

  if (isLoading) return <LoadingSpinner />

  const columns = [
    {
      key: 'order',
      header: '#',
      render: (rule: FirewallRule) => (
        <div className="flex items-center gap-1">
          <span className="text-gray-400 text-xs w-4">{rule.order_index}</span>
          <button
            onClick={(e) => {
              e.stopPropagation()
              reorderMutation.mutate({ ruleId: rule.id, direction: 'up' })
            }}
            className="p-0.5 hover:bg-gray-100 rounded"
            disabled={reorderMutation.isPending}
          >
            <ArrowUp className="w-3 h-3 text-gray-400" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation()
              reorderMutation.mutate({ ruleId: rule.id, direction: 'down' })
            }}
            className="p-0.5 hover:bg-gray-100 rounded"
            disabled={reorderMutation.isPending}
          >
            <ArrowDown className="w-3 h-3 text-gray-400" />
          </button>
        </div>
      ),
    },
    {
      key: 'name',
      header: 'Rule',
      render: (rule: FirewallRule) => (
        <div>
          <p className="font-medium text-gray-900">{rule.name}</p>
          {rule.description && <p className="text-xs text-gray-500">{rule.description}</p>}
        </div>
      ),
    },
    {
      key: 'source',
      header: 'Source',
      render: (rule: FirewallRule) => (
        <span className="text-sm text-gray-600">
          {rule.source_type === 'any' ? 'Any' : rule.source_value || rule.source_type}
        </span>
      ),
    },
    {
      key: 'dest',
      header: 'Destination',
      render: (rule: FirewallRule) => (
        <span className="text-sm text-gray-600">
          {rule.dest_type === 'any' ? 'Any' : rule.dest_value || rule.dest_type}
        </span>
      ),
    },
    {
      key: 'service',
      header: 'Service',
      render: (rule: FirewallRule) => (
        <span className="text-sm text-gray-600">
          {rule.service_protocol.toUpperCase()}{rule.service_ports ? `:${rule.service_ports}` : ''}
        </span>
      ),
    },
    {
      key: 'action',
      header: 'Action',
      render: (rule: FirewallRule) => (
        <span className={`px-2 py-0.5 rounded text-xs font-medium ${
          rule.action === 'accept'
            ? 'bg-green-100 text-green-800'
            : rule.action === 'drop'
              ? 'bg-red-100 text-red-800'
              : 'bg-orange-100 text-orange-800'
        }`}>
          {rule.action.toUpperCase()}
        </span>
      ),
    },
    {
      key: 'enabled',
      header: 'Enabled',
      render: (rule: FirewallRule) => (
        <button
          onClick={(e) => {
            e.stopPropagation()
            updateMutation.mutate({ id: rule.id, enabled: !rule.enabled })
          }}
          className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
            rule.enabled ? 'bg-primary-600' : 'bg-gray-300'
          }`}
        >
          <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
            rule.enabled ? 'translate-x-4.5' : 'translate-x-1'
          }`} />
        </button>
      ),
    },
    {
      key: 'actions',
      header: '',
      render: (rule: FirewallRule) => (
        <div className="flex items-center gap-2">
          <button
            onClick={(e) => { e.stopPropagation(); setEditTarget(rule) }}
            className="text-sm text-primary-600 hover:text-primary-700"
          >
            Edit
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); setDeleteTarget(rule) }}
            className="text-sm text-red-600 hover:text-red-700"
          >
            Delete
          </button>
        </div>
      ),
    },
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <h2 className="text-2xl font-bold text-gray-900">Firewall Rules</h2>
          <InstanceSelector />
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => deployMutation.mutate()}
            disabled={deployMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 border border-primary-600 text-primary-600 rounded-lg hover:bg-primary-50 disabled:opacity-50"
          >
            <Upload className="w-4 h-4" />
            Deploy
          </button>
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            <Plus className="w-5 h-5" />
            Add Rule
          </button>
        </div>
      </div>

      <DataTable
        columns={columns}
        data={rules || []}
        keyExtractor={(rule) => rule.id}
        emptyContent={
          <EmptyState
            icon={Shield}
            title="No firewall rules"
            description="Create your first firewall rule for this instance."
            actionLabel="Add Rule"
            onAction={() => setShowCreate(true)}
          />
        }
      />

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Add Firewall Rule" size="lg">
        <FirewallRuleForm
          onSubmit={handleCreate}
          onCancel={() => setShowCreate(false)}
          loading={createMutation.isPending}
        />
      </Modal>

      <Modal open={!!editTarget} onClose={() => setEditTarget(null)} title="Edit Firewall Rule" size="lg">
        {editTarget && (
          <FirewallRuleForm
            initial={{
              ...editTarget,
              description: editTarget.description ?? undefined,
              source_value: editTarget.source_value ?? undefined,
              dest_value: editTarget.dest_value ?? undefined,
              service_ports: editTarget.service_ports ?? undefined,
            }}
            onSubmit={handleUpdate}
            onCancel={() => setEditTarget(null)}
            loading={updateMutation.isPending}
          />
        )}
      </Modal>

      <ConfirmDialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Delete Rule"
        message={`Are you sure you want to delete "${deleteTarget?.name}"?`}
        loading={deleteMutation.isPending}
      />
    </div>
  )
}
