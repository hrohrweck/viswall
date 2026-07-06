import { useState, useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Gauge, Plus, Trash2, RefreshCw, ChevronDown, ChevronUp, Settings } from 'lucide-react'
import { api } from '../../utils/api'
import {
  useQoSPolicies,
  useDeleteQoSPolicy,
  useApplyQoSPolicy,
  useQoSStats,
  useCreateQoSPolicy,
  useUpdateQoSPolicy,
} from '../../hooks/useApi'
import type { QoSPolicy, QoSClass, QoSStats, Instance } from '../../types'

export function TrafficShaping() {
  const queryClient = useQueryClient()
  const [selectedInstanceId, setSelectedInstanceId] = useState<number | null>(null)
  const [showPolicyForm, setShowPolicyForm] = useState(false)
  const [editingPolicy, setEditingPolicy] = useState<QoSPolicy | null>(null)
  const [expandedPolicy, setExpandedPolicy] = useState<number | null>(null)

  const { data: instances = [] } = useQuery<Instance[]>({
    queryKey: ['instances'],
    queryFn: async () => {
      const res = await api.get<Instance[]>('/instances')
      return res.data
    },
  })

  useEffect(() => {
    if (!selectedInstanceId && instances.length > 0) {
      setSelectedInstanceId(instances[0].id)
    }
  }, [instances, selectedInstanceId])

  const { data: policies = [], isLoading } = useQoSPolicies(selectedInstanceId || 0)
  const deleteMutation = useDeleteQoSPolicy(selectedInstanceId || 0)
  const applyMutation = useApplyQoSPolicy(selectedInstanceId || 0)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Traffic Shaping</h2>
        <div className="flex items-center gap-3">
          <select
            value={selectedInstanceId || ''}
            onChange={(e) => setSelectedInstanceId(Number(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
          >
            {instances.map((inst) => (
              <option key={inst.id} value={inst.id}>
                {inst.name}
              </option>
            ))}
          </select>
          <button
            onClick={() => {
              setEditingPolicy(null)
              setShowPolicyForm(true)
            }}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700"
          >
            <Plus className="w-4 h-4" />
            Add Policy
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center dark:bg-gray-900 dark:border-gray-700">
          <RefreshCw className="w-8 h-8 text-gray-400 mx-auto mb-4 animate-spin" />
          <p className="text-gray-600 dark:text-gray-400">Loading QoS policies...</p>
        </div>
      ) : policies.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center dark:bg-gray-900 dark:border-gray-700">
          <Gauge className="w-16 h-16 text-gray-300 mx-auto mb-4 dark:text-gray-600" />
          <h3 className="text-lg font-medium text-gray-900 mb-2 dark:text-white">No QoS Policies</h3>
          <p className="text-gray-600 mb-4 dark:text-gray-400">
            Configure traffic shaping to prioritize critical traffic and limit bandwidth usage.
          </p>
          <button
            onClick={() => setShowPolicyForm(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700"
          >
            <Plus className="w-4 h-4" />
            Create First Policy
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {policies.map((policy) => (
            <PolicyCard
              key={policy.id}
              policy={policy}
              instanceId={selectedInstanceId!}
              isExpanded={expandedPolicy === policy.id}
              onToggleExpand={() =>
                setExpandedPolicy(expandedPolicy === policy.id ? null : policy.id)
              }
              onEdit={() => {
                setEditingPolicy(policy)
                setShowPolicyForm(true)
              }}
              onDelete={() => deleteMutation.mutate(policy.id)}
              onApply={() => applyMutation.mutate(policy.id)}
            />
          ))}
        </div>
      )}

      {showPolicyForm && (
        <PolicyFormModal
          instanceId={selectedInstanceId!}
          policy={editingPolicy}
          onClose={() => {
            setShowPolicyForm(false)
            setEditingPolicy(null)
          }}
          onSuccess={() => {
            setShowPolicyForm(false)
            setEditingPolicy(null)
            queryClient.invalidateQueries({ queryKey: ['qos-policies', selectedInstanceId] })
          }}
        />
      )}
    </div>
  )
}

interface PolicyCardProps {
  policy: QoSPolicy
  instanceId: number
  isExpanded: boolean
  onToggleExpand: () => void
  onEdit: () => void
  onDelete: () => void
  onApply: () => void
}

function PolicyCard({
  policy,
  instanceId,
  isExpanded,
  onToggleExpand,
  onEdit,
  onDelete,
  onApply,
}: PolicyCardProps) {
  const { data: stats } = useQoSStats(instanceId, policy.id, {
    enabled: policy.applied,
    refetchInterval: 30000,
  })

  const formatKbps = (kbps: number) => {
    if (kbps >= 1000000) return `${(kbps / 1000000).toFixed(1)} Gbps`
    if (kbps >= 1000) return `${(kbps / 1000).toFixed(0)} Mbps`
    return `${kbps} Kbps`
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden dark:bg-gray-900 dark:border-gray-700">
      <div className="p-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button onClick={onToggleExpand} className="text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300">
            {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-medium text-gray-900 dark:text-white">{policy.name}</h3>
              <span
                className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                  policy.enabled
                    ? policy.applied
                      ? 'bg-green-100 text-green-800 dark:bg-green-950/30 dark:text-green-400'
                      : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-950/30 dark:text-yellow-400'
                    : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400'
                }`}
              >
                {policy.enabled ? (policy.applied ? 'Active' : 'Pending') : 'Disabled'}
              </span>
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {policy.interface_name} · {policy.algorithm.toUpperCase()} · ↓{' '}
              {formatKbps(policy.download_kbps)} · ↑ {formatKbps(policy.upload_kbps)}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onApply}
            className="p-2 text-gray-400 hover:text-primary-600 hover:bg-gray-100 rounded-lg dark:text-gray-500 dark:hover:text-primary-400 dark:hover:bg-gray-800"
            title="Apply to instance"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={onEdit}
            className="p-2 text-gray-400 hover:text-primary-600 hover:bg-gray-100 rounded-lg dark:text-gray-500 dark:hover:text-primary-400 dark:hover:bg-gray-800"
            title="Edit policy"
          >
            <Settings className="w-4 h-4" />
          </button>
          <button
            onClick={onDelete}
            className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg dark:text-gray-500 dark:hover:text-red-400 dark:hover:bg-red-950/30"
            title="Delete policy"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="border-t border-gray-200 p-4 space-y-4 dark:border-gray-700">
          {policy.description && (
            <p className="text-sm text-gray-600 dark:text-gray-400">{policy.description}</p>
          )}

          {stats && <StatsPanel stats={stats} />}

          {policy.algorithm === 'htb' && policy.classes.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2 dark:text-gray-300">Traffic Classes</h4>
              <div className="space-y-2">
                {policy.classes.map((cls) => (
                  <div
                    key={cls.id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg text-sm dark:bg-gray-800"
                  >
                    <div>
                      <span className="font-medium text-gray-900 dark:text-white">{cls.name}</span>
                      <span className="ml-2 text-gray-500 dark:text-gray-400">Priority {cls.priority}</span>
                    </div>
                    <div className="text-gray-600 dark:text-gray-300">
                      {formatKbps(cls.min_rate_kbps)} - {formatKbps(cls.max_rate_kbps)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function StatsPanel({ stats }: { stats: QoSStats }) {
  const formatBytes = (bytes: number) => {
    if (bytes >= 1073741824) return `${(bytes / 1073741824).toFixed(1)} GB`
    if (bytes >= 1048576) return `${(bytes / 1048576).toFixed(1)} MB`
    if (bytes >= 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${bytes} B`
  }

  if (stats.queues.length === 0) {
    return (
      <div className="text-sm text-gray-500 dark:text-gray-400">
        No statistics available yet.
      </div>
    )
  }

  return (
    <div>
      <h4 className="text-sm font-medium text-gray-700 mb-2 dark:text-gray-300">Live Statistics</h4>
      <div className="grid grid-cols-4 gap-4">
        {stats.queues.map((queue, idx) => (
          <div key={idx} className="bg-gray-50 rounded-lg p-3 dark:bg-gray-800">
            <p className="text-xs text-gray-500 mb-1 dark:text-gray-400">{queue.qdisc || `Queue ${idx + 1}`}</p>
            <p className="text-lg font-medium text-gray-900 dark:text-white">{formatBytes(queue.sent_bytes)}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">{queue.sent_pkts} pkts</p>
            {queue.dropped_pkts > 0 && (
              <p className="text-xs text-red-600 dark:text-red-400">{queue.dropped_pkts} dropped</p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

interface PolicyFormModalProps {
  instanceId: number
  policy: QoSPolicy | null
  onClose: () => void
  onSuccess: () => void
}

function PolicyFormModal({ instanceId, policy, onClose, onSuccess }: PolicyFormModalProps) {
  const [name, setName] = useState(policy?.name || '')
  const [description, setDescription] = useState(policy?.description || '')
  const [interfaceName, setInterfaceName] = useState(policy?.interface_name || 'eth0')
  const [algorithm, setAlgorithm] = useState<'cake' | 'fq_codel' | 'htb'>(
    (policy?.algorithm as 'cake' | 'fq_codel' | 'htb') || 'cake'
  )
  const [downloadKbps, setDownloadKbps] = useState(policy?.download_kbps || 100000)
  const [uploadKbps, setUploadKbps] = useState(policy?.upload_kbps || 50000)
  const [enabled, setEnabled] = useState(policy?.enabled ?? true)

  const createMutation = useCreateQoSPolicy(instanceId)
  const updateMutation = useUpdateQoSPolicy(instanceId)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (policy) {
      updateMutation.mutate(
        {
          id: policy.id,
          name,
          description,
          enabled,
          algorithm,
          download_kbps: downloadKbps,
          upload_kbps: uploadKbps,
        },
        { onSuccess }
      )
    } else {
      createMutation.mutate(
        {
          name,
          description,
          interface_name: interfaceName,
          algorithm,
          download_kbps: downloadKbps,
          upload_kbps: uploadKbps,
          enabled,
          classes: [],
        },
        { onSuccess }
      )
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 dark:bg-black/70">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg p-6 dark:bg-gray-900 dark:border dark:border-gray-700 dark:text-white">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 dark:text-white">
          {policy ? 'Edit QoS Policy' : 'New QoS Policy'}
        </h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">Policy Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">Description</label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">Interface</label>
            <input
              type="text"
              value={interfaceName}
              onChange={(e) => setInterfaceName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
              disabled={!!policy}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">Algorithm</label>
            <select
              value={algorithm}
              onChange={(e) => setAlgorithm(e.target.value as any)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
            >
              <option value="cake">CAKE (Recommended)</option>
              <option value="fq_codel">FQ-CoDel</option>
              <option value="htb">HTB (Advanced)</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">
                Download (Kbps)
              </label>
              <input
                type="number"
                value={downloadKbps}
                onChange={(e) => setDownloadKbps(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
                min={1}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">Upload (Kbps)</label>
              <input
                type="number"
                value={uploadKbps}
                onChange={(e) => setUploadKbps(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
                min={1}
                required
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="enabled"
              checked={enabled}
              onChange={(e) => setEnabled(e.target.checked)}
              className="h-4 w-4 text-primary-600 border-gray-300 rounded"
            />
            <label htmlFor="enabled" className="text-sm text-gray-700 dark:text-gray-300">
              Enable policy immediately
            </label>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg dark:text-gray-400 dark:hover:bg-gray-800"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending || updateMutation.isPending}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50"
            >
              {createMutation.isPending ? 'Saving...' : policy ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default TrafficShaping
