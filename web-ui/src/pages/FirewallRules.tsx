import { useState } from 'react'
import { Plus, Shield, ArrowUp, ArrowDown, Upload, MoreVertical, Pencil, Trash2, Info } from 'lucide-react'
import { useInstanceStore } from '../stores/instance'
import {
  useInstances,
  useFirewallRules,
  useCreateFirewallRule,
  useUpdateFirewallRule,
  useDeleteFirewallRule,
  useReorderFirewallRule,
  useDeployFirewall,
} from '../hooks/useApi'
import {
  Badge,
  Button,
  Card,
  Checkbox,
  ConfirmDialog,
  DataTable,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  EmptyState,
  IconButton,
  Modal,
  PageHeader,
  Switch,
} from '../components/ui'
import { FirewallRuleForm } from '../components/forms/FirewallRuleForm'
import { toast } from '../components/ui/Toaster'
import { getErrMsg } from '../lib/utils'
import type { FirewallRule, FirewallRuleCreate, FirewallRuleUpdate } from '../types'
import { FirewallAction } from '../types'
import * as Dialog from '@radix-ui/react-dialog'
import { cn } from '../lib/utils'

/* ------------------------------------------------------------------ */
/*  Action → Badge variant mapping                                     */
/* ------------------------------------------------------------------ */

const actionBadge: Record<string, 'success' | 'danger' | 'warning'> = {
  accept: 'success',
  drop: 'danger',
  reject: 'warning',
}

/* ------------------------------------------------------------------ */
/*  FirewallRules                                                       */
/* ------------------------------------------------------------------ */

export function FirewallRules() {
  const { selectedInstanceId } = useInstanceStore()
  const { data: instances } = useInstances()
  const instance = instances?.find((i) => i.id === selectedInstanceId)
  const instanceName = instance?.name ?? ''

  const { data: rules, isLoading, isError, refetch } = useFirewallRules(selectedInstanceId!)
  const createMutation = useCreateFirewallRule(selectedInstanceId!)
  const updateMutation = useUpdateFirewallRule(selectedInstanceId!)
  const deleteMutation = useDeleteFirewallRule(selectedInstanceId!)
  const reorderMutation = useReorderFirewallRule(selectedInstanceId!)
  const deployMutation = useDeployFirewall(selectedInstanceId!)

  const [showCreate, setShowCreate] = useState(false)
  const [editTarget, setEditTarget] = useState<FirewallRule | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<FirewallRule | null>(null)
  const [toggleTarget, setToggleTarget] = useState<FirewallRule | null>(null)
  const [showDeploy, setShowDeploy] = useState(false)
  const [deployReviewed, setDeployReviewed] = useState(false)

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

  const handleToggle = async () => {
    if (toggleTarget) {
      updateMutation.mutate(
        { id: toggleTarget.id, enabled: !toggleTarget.enabled },
        {
          onSuccess: () => toast.success(`Rule ${toggleTarget.enabled ? 'disabled' : 'enabled'}`),
          onError: (e) => toast.error(getErrMsg(e)),
        },
      )
      setToggleTarget(null)
    }
  }

  const handleDeploy = () => {
    deployMutation.mutate(undefined, {
      onSuccess: () => {
        toast.success('Firewall rules deployed')
        setShowDeploy(false)
        setDeployReviewed(false)
      },
      onError: (e) => toast.error(getErrMsg(e)),
    })
  }

  /* ── No instance selected ── */
  if (!selectedInstanceId) {
    return (
      <div>
        <PageHeader title="Firewall Rules" />
        <Card className="mt-6">
          <div className="flex items-center gap-3 text-on-surface-muted">
            <Info className="h-5 w-5 shrink-0" />
            <p className="text-sm">Select an instance from the top bar to manage its firewall.</p>
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
      render: (rule: FirewallRule) => (
        <div className="flex items-center gap-1">
          <span className="text-on-surface-muted text-xs w-4">{rule.order_index}</span>
          <IconButton
            icon={ArrowUp}
            label="Move rule up"
            size="sm"
            variant="ghost"
            onClick={(e) => {
              e.stopPropagation()
              reorderMutation.mutate({ ruleId: rule.id, direction: 'up' })
            }}
            disabled={reorderMutation.isPending}
          />
          <IconButton
            icon={ArrowDown}
            label="Move rule down"
            size="sm"
            variant="ghost"
            onClick={(e) => {
              e.stopPropagation()
              reorderMutation.mutate({ ruleId: rule.id, direction: 'down' })
            }}
            disabled={reorderMutation.isPending}
          />
        </div>
      ),
    },
    {
      key: 'name',
      header: 'Rule',
      render: (rule: FirewallRule) => (
        <div>
          <p className="font-medium text-on-surface">{rule.name}</p>
          {rule.description && <p className="text-xs text-on-surface-muted">{rule.description}</p>}
        </div>
      ),
    },
    {
      key: 'source',
      header: 'Source',
      className: 'font-mono',
      render: (rule: FirewallRule) => (
        <span className="text-sm text-on-surface-muted">
          {rule.source_type === 'any' ? 'Any' : rule.source_value || rule.source_type}
        </span>
      ),
    },
    {
      key: 'dest',
      header: 'Destination',
      className: 'font-mono',
      render: (rule: FirewallRule) => (
        <span className="text-sm text-on-surface-muted">
          {rule.dest_type === 'any' ? 'Any' : rule.dest_value || rule.dest_type}
        </span>
      ),
    },
    {
      key: 'service',
      header: 'Service',
      className: 'font-mono',
      render: (rule: FirewallRule) => (
        <span className="text-sm text-on-surface-muted">
          {rule.service_protocol.toUpperCase()}{rule.service_ports ? `:${rule.service_ports}` : ''}
        </span>
      ),
    },
    {
      key: 'action',
      header: 'Action',
      render: (rule: FirewallRule) => (
        <Badge variant={actionBadge[rule.action] ?? 'neutral'}>
          {rule.action.toUpperCase()}
        </Badge>
      ),
    },
    {
      key: 'enabled',
      header: 'Enabled',
      render: (rule: FirewallRule) => (
        <Switch
          checked={rule.enabled}
          aria-label={`${rule.enabled ? 'Disable' : 'Enable'} rule ${rule.name}`}
          onCheckedChange={() => setToggleTarget(rule)}
        />
      ),
    },
  ]

  return (
    <div>
      <PageHeader
        title="Firewall Rules"
        description={`Managing rules for ${instanceName}`}
        secondaryActions={[
          <Button
            key="deploy"
            variant="secondary"
            icon={Upload}
            onClick={() => setShowDeploy(true)}
          >
            Deploy
          </Button>,
        ]}
        primaryAction={
          <Button icon={Plus} onClick={() => setShowCreate(true)}>
            Add Rule
          </Button>
        }
      />

      <div className="mt-6">
        <DataTable
          columns={columns}
          data={rules || []}
          keyExtractor={(rule) => rule.id}
          enableSorting
          searchable
          searchPlaceholder="Search rules…"
          isLoading={isLoading}
          isError={isError}
          onRetry={() => refetch()}
          rowActions={(rule) => (
            <DropdownMenu>
              <DropdownMenuTrigger />
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => setEditTarget(rule)}>
                  <Pencil className="h-4 w-4 mr-2" />
                  Edit
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() =>
                    reorderMutation.mutate({ ruleId: rule.id, direction: 'up' })
                  }
                >
                  <ArrowUp className="h-4 w-4 mr-2" />
                  Move up
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() =>
                    reorderMutation.mutate({ ruleId: rule.id, direction: 'down' })
                  }
                >
                  <ArrowDown className="h-4 w-4 mr-2" />
                  Move down
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem danger onClick={() => setDeleteTarget(rule)}>
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
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
      </div>

      {/* Create modal */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Add Firewall Rule" size="lg">
        <FirewallRuleForm
          onSubmit={handleCreate}
          onCancel={() => setShowCreate(false)}
          loading={createMutation.isPending}
        />
      </Modal>

      {/* Edit modal */}
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

      {/* Delete confirm */}
      <ConfirmDialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Delete Rule"
        message={`Are you sure you want to delete "${deleteTarget?.name}"?`}
        confirmLabel="Delete"
        loading={deleteMutation.isPending}
        variant="danger"
      />

      {/* Enable/disable toggle confirm */}
      <ConfirmDialog
        open={!!toggleTarget}
        onClose={() => setToggleTarget(null)}
        onConfirm={handleToggle}
        title={toggleTarget?.enabled ? 'Disable Rule' : 'Enable Rule'}
        message={
          toggleTarget?.enabled
            ? `Disable rule '${toggleTarget?.name}'? Traffic matching this rule may be blocked/allowed differently.`
            : `Enable rule '${toggleTarget?.name}'?`
        }
        confirmLabel={toggleTarget?.enabled ? 'Disable' : 'Enable'}
        loading={updateMutation.isPending}
        variant="warning"
      />

      {/* Deploy confirm — composed manually because ConfirmDialog has no checkbox.
          Review checkbox gates the confirm button per the deploy-safety pattern. */}
      <Dialog.Root
        open={showDeploy}
        onOpenChange={(nextOpen) => {
          if (!nextOpen) {
            setShowDeploy(false)
            setDeployReviewed(false)
          }
        }}
      >
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-50 bg-black/50" />
          <Dialog.Content
            aria-modal="true"
            className={cn(
              'fixed left-1/2 top-1/2 z-50 -translate-x-1/2 -translate-y-1/2',
              'w-full max-w-md mx-4',
              'bg-surface-card text-on-surface border border-border rounded-card shadow-xl',
              'focus:outline-none',
            )}
          >
            <div className="p-6">
              <Dialog.Title className="text-lg font-semibold text-on-surface">
                Deploy Firewall Rules
              </Dialog.Title>
              <Dialog.Description className="text-on-surface-muted mt-2">
                Applies {rules?.length ?? 0} rules to {instanceName}. Connections not matching the
                ruleset will be dropped.
              </Dialog.Description>
              <label className="flex items-center gap-2 mt-4 cursor-pointer">
                <Checkbox
                  checked={deployReviewed}
                  onChange={(e) => setDeployReviewed(e.target.checked)}
                />
                <span className="text-sm text-on-surface">
                  I have reviewed the pending changes
                </span>
              </label>
              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => {
                    setShowDeploy(false)
                    setDeployReviewed(false)
                  }}
                  disabled={deployMutation.isPending}
                  className="px-4 py-2 text-on-surface-muted bg-surface-elevated border border-border rounded-lg hover:text-on-surface hover:bg-surface disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeploy}
                  disabled={!deployReviewed || deployMutation.isPending}
                  className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50"
                >
                  {deployMutation.isPending ? 'Deploying…' : 'Deploy'}
                </button>
              </div>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </div>
  )
}
