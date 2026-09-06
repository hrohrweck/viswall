import { useState } from 'react'
import { Gauge, Plus, Trash2, RefreshCw, ChevronDown, ChevronUp, Settings, Info } from 'lucide-react'
import { useInstanceStore } from '../../stores/instance'
import {
  useInstances,
  useQoSPolicies,
  useDeleteQoSPolicy,
  useApplyQoSPolicy,
  useQoSStats,
  useCreateQoSPolicy,
  useUpdateQoSPolicy,
} from '../../hooks/useApi'
import {
  Badge,
  Button,
  Card,
  CardBody,
  CardHeader,
  CardTitle,
  CardActions,
  ConfirmDialog,
  IconButton,
  Modal,
  PageHeader,
} from '../../components/ui'
import { TrafficPolicyForm } from '../../components/forms/TrafficPolicyForm'
import { toast } from '../../components/ui/Toaster'
import { getErrMsg } from '../../lib/utils'
import type { QoSPolicy, QoSPolicyCreate, QoSPolicyUpdate, QoSStats } from '../../types'

/* ------------------------------------------------------------------ */
/*  TrafficShaping                                                     */
/* ------------------------------------------------------------------ */

export function TrafficShaping() {
  const { selectedInstanceId } = useInstanceStore()
  const { data: instances } = useInstances()
  const instance = instances?.find((i) => i.id === selectedInstanceId)
  const instanceName = instance?.name ?? ''

  const [showPolicyForm, setShowPolicyForm] = useState(false)
  const [editingPolicy, setEditingPolicy] = useState<QoSPolicy | null>(null)
  const [expandedPolicy, setExpandedPolicy] = useState<number | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<QoSPolicy | null>(null)
  const [applyTarget, setApplyTarget] = useState<QoSPolicy | null>(null)

  const { data: policies = [], isLoading, isError, refetch } = useQoSPolicies(selectedInstanceId || 0)
  const deleteMutation = useDeleteQoSPolicy(selectedInstanceId || 0)
  const applyMutation = useApplyQoSPolicy(selectedInstanceId || 0)
  const createMutation = useCreateQoSPolicy(selectedInstanceId || 0)
  const updateMutation = useUpdateQoSPolicy(selectedInstanceId || 0)

  const handleCreate = async (data: QoSPolicyCreate | QoSPolicyUpdate) => {
    await createMutation.mutateAsync(data as QoSPolicyCreate)
    setShowPolicyForm(false)
    toast.success('QoS policy created')
  }

  const handleUpdate = async (data: QoSPolicyUpdate) => {
    if (editingPolicy) {
      await updateMutation.mutateAsync({ id: editingPolicy.id, ...data })
      setEditingPolicy(null)
      setShowPolicyForm(false)
      toast.success('QoS policy updated')
    }
  }

  const handleDelete = async () => {
    if (deleteTarget) {
      await deleteMutation.mutateAsync(deleteTarget.id)
      setDeleteTarget(null)
      toast.success(`Deleted policy "${deleteTarget.name}"`)
    }
  }

  const handleApply = async () => {
    if (applyTarget) {
      await applyMutation.mutateAsync(applyTarget.id)
      setApplyTarget(null)
      toast.success(`Applied policy "${applyTarget.name}"`)
    }
  }

  /* ── No instance selected ── */
  if (!selectedInstanceId) {
    return (
      <div>
        <PageHeader title="Traffic Shaping" />
        <Card className="mt-6">
          <div className="flex items-center gap-3 text-on-surface-muted">
            <Info className="h-5 w-5 shrink-0" />
            <p className="text-sm">Select an instance from the top bar to manage traffic shaping.</p>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div>
      <PageHeader
        title="Traffic Shaping"
        description={instanceName ? `Manage QoS policies for ${instanceName}` : 'Configure traffic shaping policies'}
        primaryAction={
          <Button
            icon={Plus}
            onClick={() => {
              setEditingPolicy(null)
              setShowPolicyForm(true)
            }}
          >
            Add Policy
          </Button>
        }
      />

      <div className="mt-6 space-y-4">
        {isLoading ? (
          <Card>
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <RefreshCw className="w-8 h-8 text-on-surface-muted mx-auto mb-4 animate-spin" />
              <p className="text-on-surface-muted">Loading QoS policies...</p>
            </div>
          </Card>
        ) : isError ? (
          <Card>
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <p className="text-danger mb-4">Failed to load QoS policies</p>
              <Button variant="secondary" onClick={() => refetch()}>Retry</Button>
            </div>
          </Card>
        ) : policies.length === 0 ? (
          <Card>
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Gauge className="w-16 h-16 text-on-surface-muted mx-auto mb-4" />
              <h3 className="text-lg font-medium text-on-surface mb-2">No QoS Policies</h3>
              <p className="text-on-surface-muted mb-4">
                Configure traffic shaping to prioritize critical traffic and limit bandwidth usage.
              </p>
              <Button
                icon={Plus}
                onClick={() => {
                  setEditingPolicy(null)
                  setShowPolicyForm(true)
                }}
              >
                Create First Policy
              </Button>
            </div>
          </Card>
        ) : (
          policies.map((policy) => (
            <PolicyCard
              key={policy.id}
              policy={policy}
              instanceId={selectedInstanceId}
              instanceName={instanceName}
              isExpanded={expandedPolicy === policy.id}
              onToggleExpand={() =>
                setExpandedPolicy(expandedPolicy === policy.id ? null : policy.id)
              }
              onEdit={() => {
                setEditingPolicy(policy)
                setShowPolicyForm(true)
              }}
              onDelete={() => setDeleteTarget(policy)}
              onApply={() => setApplyTarget(policy)}
            />
          ))
        )}
      </div>

      {/* Create / Edit modal */}
      <Modal
        open={showPolicyForm}
        onClose={() => { setShowPolicyForm(false); setEditingPolicy(null) }}
        title={editingPolicy ? 'Edit QoS Policy' : 'New QoS Policy'}
      >
        <TrafficPolicyForm
          initial={editingPolicy || undefined}
          onSubmit={editingPolicy ? handleUpdate : handleCreate}
          onCancel={() => { setShowPolicyForm(false); setEditingPolicy(null) }}
          loading={createMutation.isPending || updateMutation.isPending}
        />
      </Modal>

      {/* Delete confirm */}
      <ConfirmDialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Delete QoS Policy"
        message={`Deletes policy "${deleteTarget?.name}" from ${instanceName}.`}
        loading={deleteMutation.isPending}
      />

      {/* Apply confirm */}
      <ConfirmDialog
        open={!!applyTarget}
        onClose={() => setApplyTarget(null)}
        onConfirm={handleApply}
        title="Apply QoS Policy"
        message={`Applies policy "${applyTarget?.name}" to ${instanceName}.`}
        impact="Active connections may be affected."
        confirmLabel="Apply"
        variant="warning"
        loading={applyMutation.isPending}
      />
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  PolicyCard                                                         */
/* ------------------------------------------------------------------ */

interface PolicyCardProps {
  policy: QoSPolicy
  instanceId: number
  instanceName: string
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

  const statusVariant = policy.enabled
    ? policy.applied
      ? 'success'
      : 'warning'
    : 'neutral'

  const statusLabel = policy.enabled
    ? policy.applied ? 'Active' : 'Pending'
    : 'Disabled'

  return (
    <Card>
      <CardHeader
        title={
          <div className="flex items-center gap-2">
            <button
              onClick={onToggleExpand}
              aria-label={isExpanded ? `Collapse ${policy.name}` : `Expand ${policy.name}`}
              className="text-on-surface-muted hover:text-on-surface"
            >
              {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
            </button>
            <CardTitle>{policy.name}</CardTitle>
            <Badge variant={statusVariant}>{statusLabel}</Badge>
          </div>
        }
        actions={
          <CardActions>
            <IconButton
              icon={RefreshCw}
              label="Apply to instance"
              size="sm"
              onClick={onApply}
            />
            <IconButton
              icon={Settings}
              label="Edit policy"
              size="sm"
              onClick={onEdit}
            />
            <IconButton
              icon={Trash2}
              label="Delete policy"
              variant="destructive"
              size="sm"
              onClick={onDelete}
            />
          </CardActions>
        }
      />
      <CardBody>
        <p className="text-sm text-on-surface-muted">
          {policy.interface_name} · {policy.algorithm.toUpperCase()} · ↓{' '}
          {formatKbps(policy.download_kbps)} · ↑ {formatKbps(policy.upload_kbps)}
        </p>

        {isExpanded && (
          <div className="mt-4 space-y-4">
            {policy.description && (
              <p className="text-sm text-on-surface-muted">{policy.description}</p>
            )}

            {stats && <StatsPanel stats={stats} />}

            {policy.algorithm === 'htb' && policy.classes.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-on-surface mb-2">Traffic Classes</h4>
                <div className="space-y-2">
                  {policy.classes.map((cls) => (
                    <div
                      key={cls.id}
                      className="flex items-center justify-between p-3 bg-surface-elevated rounded-card text-sm"
                    >
                      <div>
                        <span className="font-medium text-on-surface">{cls.name}</span>
                        <span className="ml-2 text-on-surface-muted">Priority {cls.priority}</span>
                      </div>
                      <div className="text-on-surface-muted">
                        {formatKbps(cls.min_rate_kbps)} - {formatKbps(cls.max_rate_kbps)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </CardBody>
    </Card>
  )
}

/* ------------------------------------------------------------------ */
/*  StatsPanel                                                         */
/* ------------------------------------------------------------------ */

function StatsPanel({ stats }: { stats: QoSStats }) {
  const formatBytes = (bytes: number) => {
    if (bytes >= 1073741824) return `${(bytes / 1073741824).toFixed(1)} GB`
    if (bytes >= 1048576) return `${(bytes / 1048576).toFixed(1)} MB`
    if (bytes >= 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${bytes} B`
  }

  if (stats.queues.length === 0) {
    return (
      <p className="text-sm text-on-surface-muted">No statistics available yet.</p>
    )
  }

  return (
    <div>
      <h4 className="text-sm font-medium text-on-surface mb-2">Live Statistics</h4>
      <div className="grid grid-cols-4 gap-4">
        {stats.queues.map((queue, idx) => (
          <div key={idx} className="bg-surface-elevated rounded-card p-3">
            <p className="text-xs text-on-surface-muted mb-1">{queue.qdisc || `Queue ${idx + 1}`}</p>
            <p className="text-lg font-medium text-on-surface">{formatBytes(queue.sent_bytes)}</p>
            <p className="text-xs text-on-surface-muted">{queue.sent_pkts} pkts</p>
            {queue.dropped_pkts > 0 && (
              <p className="text-xs text-danger">{queue.dropped_pkts} dropped</p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default TrafficShaping
