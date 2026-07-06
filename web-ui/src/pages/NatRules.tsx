import { useState } from 'react'
import { Plus, Globe, ArrowRightLeft } from 'lucide-react'
import { useInstanceStore } from '../stores/instance'
import { useNATRules, useCreateNATRule } from '../hooks/useApi'
import {
  InstanceSelector,
  DataTable,
  Modal,
  EmptyState,
  LoadingSpinner,
} from '../components/ui'
import type { NATRule, NATRuleCreate } from '../types'
import { NATType } from '../types'

export function NatRules() {
  const { selectedInstanceId } = useInstanceStore()
  const { data: rules, isLoading } = useNATRules(selectedInstanceId || 0)
  const createMutation = useCreateNATRule(selectedInstanceId || 0)

  const [showCreate, setShowCreate] = useState(false)

  const handleCreate = async (data: NATRuleCreate) => {
    await createMutation.mutateAsync(data)
    setShowCreate(false)
  }

  if (!selectedInstanceId) {
    return (
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6 dark:text-white">NAT Rules</h2>
        <EmptyState
          icon={Globe}
          title="Select an Instance"
          description="Choose an instance from the dropdown above to manage its NAT rules."
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
      key: 'name',
      header: 'Rule',
      render: (rule: NATRule) => (
        <div>
          <p className="font-medium text-gray-900 dark:text-white">{rule.name}</p>
          {rule.description && <p className="text-xs text-gray-500 dark:text-gray-400">{rule.description}</p>}
        </div>
      ),
    },
    {
      key: 'type',
      header: 'Type',
      render: (rule: NATRule) => (
        <span className="px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-950/30 dark:text-blue-400">
          {rule.type.toUpperCase()}
        </span>
      ),
    },
    {
      key: 'interface',
      header: 'Interface',
      render: (rule: NATRule) => (
        <span className="text-sm text-gray-600 dark:text-gray-400">{rule.interface || 'Any'}</span>
      ),
    },
    {
      key: 'source',
      header: 'Source',
      render: (rule: NATRule) => (
        <span className="text-sm text-gray-600 dark:text-gray-400">{rule.source_network || 'Any'}</span>
      ),
    },
    {
      key: 'dest',
      header: 'Destination',
      render: (rule: NATRule) => (
        <span className="text-sm text-gray-600 dark:text-gray-400">{rule.dest_network || 'Any'}</span>
      ),
    },
    {
      key: 'translation',
      header: 'Translation',
      render: (rule: NATRule) => (
        <span className="text-sm text-gray-600 dark:text-gray-400">
          {rule.to_source || rule.to_destination || '-'}
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (rule: NATRule) => (
        <span
          className={`px-2 py-0.5 rounded text-xs font-medium ${
            rule.enabled
              ? 'bg-green-100 text-green-800 dark:bg-green-950/30 dark:text-green-400'
              : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400'
          }`}
        >
          {rule.enabled ? 'Enabled' : 'Disabled'}
        </span>
      ),
    },
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">NAT Rules</h2>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700"
        >
          <Plus className="w-4 h-4" />
          Add NAT Rule
        </button>
      </div>

      {rules && rules.length > 0 ? (
        <DataTable columns={columns} data={rules} keyExtractor={(rule) => rule.id} />
      ) : (
        <EmptyState
          icon={ArrowRightLeft}
          title="No NAT Rules"
          description="Create NAT rules to translate source or destination addresses for traffic flowing through this instance."
        />
      )}

      {showCreate && (
        <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Create NAT Rule">
          <NATRuleForm
            onSubmit={handleCreate}
            onCancel={() => setShowCreate(false)}
            isSubmitting={createMutation.isPending}
          />
        </Modal>
      )}
    </div>
  )
}

interface NATRuleFormProps {
  onSubmit: (data: NATRuleCreate) => void
  onCancel: () => void
  isSubmitting: boolean
}

function NATRuleForm({ onSubmit, onCancel, isSubmitting }: NATRuleFormProps) {
  const [formData, setFormData] = useState<NATRuleCreate>({
    name: '',
    type: NATType.SNAT,
    enabled: true,
    interface: '',
    source_network: '',
    dest_network: '',
    to_source: '',
    to_destination: '',
    service_protocol: 'any',
    service_ports: '',
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">Name</label>
        <input
          type="text"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">Type</label>
        <select
          value={formData.type}
          onChange={(e) => setFormData({ ...formData, type: e.target.value as NATType })}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
        >
          <option value={NATType.SNAT}>Source NAT (SNAT)</option>
          <option value={NATType.DNAT}>Destination NAT (DNAT)</option>
          <option value={NATType.MASQUERADE}>Masquerade</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">Interface</label>
        <input
          type="text"
          value={formData.interface}
          onChange={(e) => setFormData({ ...formData, interface: e.target.value })}
          placeholder="e.g. eth0"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">Source Network</label>
          <input
            type="text"
            value={formData.source_network}
            onChange={(e) => setFormData({ ...formData, source_network: e.target.value })}
            placeholder="e.g. 192.168.1.0/24"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">Destination Network</label>
          <input
            type="text"
            value={formData.dest_network}
            onChange={(e) => setFormData({ ...formData, dest_network: e.target.value })}
            placeholder="e.g. 10.0.0.0/8"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
          />
        </div>
      </div>

      {formData.type !== 'masquerade' && (
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">
              {formData.type === 'snat' ? 'To Source' : 'To Destination'}
            </label>
            <input
              type="text"
              value={formData.type === 'snat' ? formData.to_source : formData.to_destination}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  ...(formData.type === 'snat'
                    ? { to_source: e.target.value }
                    : { to_destination: e.target.value }),
                })
              }
              placeholder="e.g. 203.0.113.1"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
            />
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">Protocol</label>
          <select
            value={formData.service_protocol}
            onChange={(e) => setFormData({ ...formData, service_protocol: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm dark:bg-gray-800 dark:border-gray-600 dark:text-white"
          >
            <option value="any">Any</option>
            <option value="tcp">TCP</option>
            <option value="udp">UDP</option>
            <option value="icmp">ICMP</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">Ports</label>
          <input
            type="text"
            value={formData.service_ports}
            onChange={(e) => setFormData({ ...formData, service_ports: e.target.value })}
            placeholder="e.g. 80,443"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
          />
        </div>
      </div>

      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="nat-enabled"
          checked={formData.enabled}
          onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
          className="h-4 w-4 text-primary-600 border-gray-300 rounded"
        />
        <label htmlFor="nat-enabled" className="text-sm text-gray-700 dark:text-gray-300">
          Enable rule
        </label>
      </div>

      <div className="flex justify-end gap-3 pt-4">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg dark:text-gray-400 dark:hover:bg-gray-800"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isSubmitting}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50"
        >
          {isSubmitting ? 'Creating...' : 'Create'}
        </button>
      </div>
    </form>
  )
}
