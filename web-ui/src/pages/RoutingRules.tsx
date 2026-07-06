import { useState } from 'react'
import { Plus, Route, Upload, ArrowUp, ArrowDown } from 'lucide-react'
import { useInstanceStore } from '../stores/instance'
import {
  useRoutingRules,
  useCreateRoutingRule,
  useUpdateRoutingRule,
  useDeleteRoutingRule,
  useApplyRouting,
} from '../hooks/useApi'
import {
  InstanceSelector,
  DataTable,
  Modal,
  ConfirmDialog,
  EmptyState,
  LoadingSpinner,
} from '../components/ui'
import type { RoutingRule, RoutingRuleCreate, RoutingRuleUpdate } from '../types'

export function RoutingRules() {
  const { selectedInstanceId } = useInstanceStore()
  const { data: rules, isLoading } = useRoutingRules(selectedInstanceId!)
  const createMutation = useCreateRoutingRule(selectedInstanceId!)
  const updateMutation = useUpdateRoutingRule(selectedInstanceId!)
  const deleteMutation = useDeleteRoutingRule(selectedInstanceId!)
  const applyMutation = useApplyRouting(selectedInstanceId!)

  const [showCreate, setShowCreate] = useState(false)
  const [editTarget, setEditTarget] = useState<RoutingRule | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<RoutingRule | null>(null)

  const handleCreate = async (data: RoutingRuleCreate) => {
    await createMutation.mutateAsync(data)
    setShowCreate(false)
  }

  const handleUpdate = async (data: RoutingRuleUpdate) => {
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

  const handleApply = async () => {
    await applyMutation.mutateAsync()
  }

  if (!selectedInstanceId) {
    return (
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6 dark:text-white">Routing Rules</h2>
        <EmptyState
          icon={Route}
          title="Select an Instance"
          description="Choose an instance from the dropdown above to manage its routing rules."
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
      render: (rule: RoutingRule) => (
        <span className="text-gray-400 text-xs w-4 dark:text-gray-500">{rule.order_index}</span>
      ),
    },
    {
      key: 'name',
      header: 'Name',
      render: (rule: RoutingRule) => (
        <div>
          <p className="font-medium text-gray-900 dark:text-white">{rule.name}</p>
        </div>
      ),
    },
    {
      key: 'match',
      header: 'Match Conditions',
      render: (rule: RoutingRule) => (
        <div className="text-sm text-gray-600 space-y-0.5 dark:text-gray-400">
          {rule.source_network && <span>Src: {rule.source_network}</span>}
          {rule.dest_network && <span>Dst: {rule.dest_network}</span>}
          {rule.service && <span>Service: {rule.service}</span>}
          {rule.inbound_interface && <span>In: {rule.inbound_interface}</span>}
          {!rule.source_network && !rule.dest_network && !rule.service && !rule.inbound_interface && (
            <span className="text-gray-400 dark:text-gray-500">Any</span>
          )}
        </div>
      ),
    },
    {
      key: 'action',
      header: 'Action',
      render: (rule: RoutingRule) => (
        <div className="text-sm text-gray-600 space-y-0.5 dark:text-gray-400">
          {rule.gateway && <span>Gateway: {rule.gateway}</span>}
          {rule.outbound_interface && <span>Out: {rule.outbound_interface}</span>}
          {rule.mark && <span>Mark: {rule.mark}</span>}
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (rule: RoutingRule) => (
        <span className={`px-2 py-0.5 rounded text-xs ${rule.enabled ? 'bg-green-100 text-green-700 dark:bg-green-950/30 dark:text-green-400' : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'}`}>
          {rule.enabled ? 'Enabled' : 'Disabled'}
        </span>
      ),
    },
    {
      key: 'actions',
      header: '',
      render: (rule: RoutingRule) => (
        <div className="flex items-center gap-2">
          <button
            onClick={() => setEditTarget(rule)}
            className="text-sm text-primary-600 hover:text-primary-700"
          >
            Edit
          </button>
          <button
            onClick={() => setDeleteTarget(rule)}
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
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Routing Rules</h2>
        <div className="flex items-center gap-2">
          <InstanceSelector />
        </div>
      </div>

      <div className="flex items-center gap-2 mb-4">
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm"
        >
          <Plus className="w-4 h-4" />
          Add Rule
        </button>
        <button
          onClick={handleApply}
          disabled={applyMutation.isPending}
          className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 text-sm disabled:opacity-50 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-700"
        >
          <Upload className="w-4 h-4" />
          {applyMutation.isPending ? 'Applying...' : 'Apply Rules'}
        </button>
      </div>

      <DataTable
        columns={columns}
        data={rules || []}
        keyExtractor={(rule) => rule.id}
        emptyContent={
          <EmptyState
            icon={Route}
            title="No Routing Rules"
            description="Create your first routing rule to manage traffic flow."
            actionLabel="Add Rule"
            onAction={() => setShowCreate(true)}
          />
        }
      />

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Create Routing Rule">
        <RoutingRuleForm
          onSubmit={handleCreate}
          onCancel={() => setShowCreate(false)}
          loading={createMutation.isPending}
        />
      </Modal>

      <Modal open={!!editTarget} onClose={() => setEditTarget(null)} title="Edit Routing Rule">
        {editTarget && (
          <RoutingRuleForm
            initial={editTarget}
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
        title="Delete Routing Rule"
        message={`Are you sure you want to delete "${deleteTarget?.name}"?`}
        loading={deleteMutation.isPending}
      />
    </div>
  )
}

// Routing Rule Form Component
interface RoutingRuleFormProps {
  initial?: RoutingRule
  onSubmit: (data: RoutingRuleCreate) => void
  onCancel: () => void
  loading: boolean
}

function RoutingRuleForm({ initial, onSubmit, onCancel, loading }: RoutingRuleFormProps) {
  const [form, setForm] = useState<RoutingRuleCreate>({
    name: initial?.name || '',
    enabled: initial?.enabled ?? true,
    source_network: initial?.source_network || '',
    dest_network: initial?.dest_network || '',
    service: initial?.service || '',
    inbound_interface: initial?.inbound_interface || '',
    gateway: initial?.gateway || '',
    outbound_interface: initial?.outbound_interface || '',
    mark: initial?.mark,
    order_index: initial?.order_index,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(form)
  }

  const inputClass = "w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">Name</label>
        <input
          type="text"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          className={inputClass}
          placeholder="e.g. Route DMZ to WAN"
          required
        />
      </div>

      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="enabled"
          checked={form.enabled}
          onChange={(e) => setForm({ ...form, enabled: e.target.checked })}
          className="w-4 h-4"
        />
        <label htmlFor="enabled" className="text-sm text-gray-700 dark:text-gray-300">Enabled</label>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">Source Network</label>
          <input
            type="text"
            value={form.source_network || ''}
            onChange={(e) => setForm({ ...form, source_network: e.target.value || undefined })}
            className={inputClass}
            placeholder="10.0.0.0/24 or 2001:db8::/64"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">Dest Network</label>
          <input
            type="text"
            value={form.dest_network || ''}
            onChange={(e) => setForm({ ...form, dest_network: e.target.value || undefined })}
            className={inputClass}
            placeholder="0.0.0.0/0 or ::/0"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">Service</label>
          <input
            type="text"
            value={form.service || ''}
            onChange={(e) => setForm({ ...form, service: e.target.value || undefined })}
            className={inputClass}
            placeholder="tcp/80"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">Inbound Interface</label>
          <input
            type="text"
            value={form.inbound_interface || ''}
            onChange={(e) => setForm({ ...form, inbound_interface: e.target.value || undefined })}
            className={inputClass}
            placeholder="eth0"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">Gateway</label>
          <input
            type="text"
            value={form.gateway || ''}
            onChange={(e) => setForm({ ...form, gateway: e.target.value || undefined })}
            className={inputClass}
            placeholder="192.168.1.1 or 2001:db8::1"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">Outbound Interface</label>
          <input
            type="text"
            value={form.outbound_interface || ''}
            onChange={(e) => setForm({ ...form, outbound_interface: e.target.value || undefined })}
            className={inputClass}
            placeholder="eth1"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">Firewall Mark (fwmark)</label>
        <input
          type="number"
          value={form.mark || ''}
          onChange={(e) => setForm({ ...form, mark: e.target.value ? parseInt(e.target.value) : undefined })}
          className={inputClass}
          placeholder="100"
        />
      </div>

      <div className="flex items-center justify-end gap-2 pt-4">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-gray-700 hover:bg-gray-50 rounded-lg text-sm dark:text-gray-400 dark:hover:bg-gray-800"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm disabled:opacity-50"
        >
          {loading ? 'Saving...' : initial ? 'Update' : 'Create'}
        </button>
      </div>
    </form>
  )
}
