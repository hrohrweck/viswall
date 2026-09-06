import { useState } from 'react'
import { Plus, Route, Upload, Info } from 'lucide-react'
import { useInstanceStore } from '../stores/instance'
import {
  useInstances,
  useRoutingRules,
  useCreateRoutingRule,
  useUpdateRoutingRule,
  useDeleteRoutingRule,
  useApplyRouting,
} from '../hooks/useApi'
import {
  Badge,
  Button,
  Card,
  ConfirmDialog,
  DataTable,
  Modal,
  PageHeader,
} from '../components/ui'
import { RoutingRuleForm } from '../components/forms/RoutingRuleForm'
import { toast } from '../components/ui/Toaster'
import { getErrMsg } from '../lib/utils'
import type { RoutingRule, RoutingRuleCreate, RoutingRuleUpdate } from '../types'

/* ------------------------------------------------------------------ */
/*  RoutingRules                                                       */
/* ------------------------------------------------------------------ */

export function RoutingRules() {
  const { selectedInstanceId } = useInstanceStore()
  const { data: instances } = useInstances()
  const instance = instances?.find((i) => i.id === selectedInstanceId)
  const instanceName = instance?.name ?? ''

  const { data: rules, isLoading, isError, refetch } = useRoutingRules(selectedInstanceId!)
  const createMutation = useCreateRoutingRule(selectedInstanceId!)
  const updateMutation = useUpdateRoutingRule(selectedInstanceId!)
  const deleteMutation = useDeleteRoutingRule(selectedInstanceId!)
  const applyMutation = useApplyRouting(selectedInstanceId!)

  const [showCreate, setShowCreate] = useState(false)
  const [editTarget, setEditTarget] = useState<RoutingRule | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<RoutingRule | null>(null)
  const [showApplyConfirm, setShowApplyConfirm] = useState(false)

  const handleCreate = async (data: RoutingRuleCreate | RoutingRuleUpdate) => {
    await createMutation.mutateAsync(data as RoutingRuleCreate)
    setShowCreate(false)
    toast.success('Routing rule created')
  }

  const handleUpdate = async (data: RoutingRuleUpdate) => {
    if (editTarget) {
      await updateMutation.mutateAsync({ id: editTarget.id, ...data })
      setEditTarget(null)
      toast.success('Routing rule updated')
    }
  }

  const handleDelete = async () => {
    if (deleteTarget) {
      await deleteMutation.mutateAsync(deleteTarget.id)
      setDeleteTarget(null)
      toast.success('Routing rule deleted')
    }
  }

  const handleApply = async () => {
    await applyMutation.mutateAsync()
    setShowApplyConfirm(false)
    toast.success('Routing policy applied')
  }

  /* ── No instance selected ── */
  if (!selectedInstanceId) {
    return (
      <div>
        <PageHeader title="Routing Rules" />
        <Card className="mt-6">
          <div className="flex items-center gap-3 text-on-surface-muted">
            <Info className="h-5 w-5 shrink-0" />
            <p className="text-sm">Select an instance from the top bar to manage routing rules.</p>
          </div>
        </Card>
      </div>
    )
  }

  /* ── Columns ── */
  const columns = [
    {
      key: 'order',
      header: '#',
      render: (rule: RoutingRule) => (
        <span className="text-on-surface-muted text-xs w-4">{rule.order_index}</span>
      ),
    },
    {
      key: 'name',
      header: 'Name',
      render: (rule: RoutingRule) => (
        <p className="font-medium text-on-surface">{rule.name}</p>
      ),
    },
    {
      key: 'match',
      header: 'Match Conditions',
      render: (rule: RoutingRule) => (
        <div className="text-sm text-on-surface-muted space-y-0.5">
          {rule.source_network && <span>Src: {rule.source_network}</span>}
          {rule.dest_network && <span>Dst: {rule.dest_network}</span>}
          {rule.service && <span>Service: {rule.service}</span>}
          {rule.inbound_interface && <span>In: {rule.inbound_interface}</span>}
          {!rule.source_network && !rule.dest_network && !rule.service && !rule.inbound_interface && (
            <span className="text-on-surface-muted">Any</span>
          )}
        </div>
      ),
    },
    {
      key: 'action',
      header: 'Action',
      render: (rule: RoutingRule) => (
        <div className="text-sm text-on-surface-muted space-y-0.5">
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
        <Badge variant={rule.enabled ? 'success' : 'neutral'}>
          {rule.enabled ? 'Enabled' : 'Disabled'}
        </Badge>
      ),
    },
    {
      key: 'actions',
      header: '',
      render: (rule: RoutingRule) => (
        <div className="flex items-center gap-2">
          <button
            onClick={(e) => { e.stopPropagation(); setEditTarget(rule) }}
            className="text-sm text-primary hover:text-primary-hover"
          >
            Edit
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); setDeleteTarget(rule) }}
            className="text-sm text-danger hover:text-danger/80"
          >
            Delete
          </button>
        </div>
      ),
    },
  ]

  return (
    <div>
      <PageHeader
        title="Routing Rules"
        description={instanceName ? `Manage routing rules for ${instanceName}` : 'Manage policy routing rules'}
        primaryAction={
          <Button icon={Plus} onClick={() => setShowCreate(true)}>
            Add Rule
          </Button>
        }
        secondaryActions={[
          <Button
            key="apply"
            variant="secondary"
            icon={Upload}
            loading={applyMutation.isPending}
            onClick={() => setShowApplyConfirm(true)}
          >
            Apply Rules
          </Button>,
        ]}
      />

      <div className="mt-6">
        <DataTable
          columns={columns}
          data={rules || []}
          keyExtractor={(rule) => rule.id}
          enableSorting
          searchable
          searchPlaceholder="Search rules..."
          isLoading={isLoading}
          isError={isError}
          onRetry={() => refetch()}
          emptyContent={
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Route className="h-10 w-10 text-on-surface-muted mb-3" />
              <p className="text-sm text-on-surface-muted mb-2">No Routing Rules</p>
              <p className="text-xs text-on-surface-muted mb-4">Create your first routing rule to manage traffic flow.</p>
              <Button icon={Plus} onClick={() => setShowCreate(true)}>
                Add Rule
              </Button>
            </div>
          }
        />
      </div>

      {/* Create modal */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Create Routing Rule">
        <RoutingRuleForm
          onSubmit={handleCreate}
          onCancel={() => setShowCreate(false)}
          loading={createMutation.isPending}
        />
      </Modal>

      {/* Edit modal */}
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

      {/* Delete confirm */}
      <ConfirmDialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Delete Routing Rule"
        message={`Are you sure you want to delete "${deleteTarget?.name}"?`}
        loading={deleteMutation.isPending}
      />

      {/* Apply confirm */}
      <ConfirmDialog
        open={showApplyConfirm}
        onClose={() => setShowApplyConfirm(false)}
        onConfirm={handleApply}
        title="Apply Routing Policy"
        message={`Applies routing policy to ${instanceName}.`}
        impact="Active connections may be re-routed."
        confirmLabel="Apply"
        variant="warning"
        loading={applyMutation.isPending}
      />
    </div>
  )
}
