import { useState } from 'react'
import {
  Cable,
  Download,
  Info,
  Plus,
  ScanSearch,
  Upload,
} from 'lucide-react'
import { useInstanceStore } from '../stores/instance'
import {
  useInstances,
  useNetworkInterfaces,
  useLiveNetworkInterfaces,
  useCreateNetworkInterface,
  useUpdateNetworkInterface,
  useDeleteNetworkInterface,
  useApplyNetworkInterfaces,
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
import { InterfaceForm } from '../components/forms/InterfaceForm'
import { toast } from '../components/ui/Toaster'
import { getErrMsg } from '../lib/utils'
import { useAuthStore } from '../stores/auth'
import type {
  InterfaceApplyResult,
  InterfaceLiveState,
  NetworkInterface,
  NetworkInterfaceCreate,
  NetworkInterfaceUpdate,
} from '../types'

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function addrList(iface: InterfaceLiveState): string {
  return iface.addresses.map((a) => `${a.address}/${a.prefixlen}`).join(', ')
}

function ApplyResultCard({ result }: { result: InterfaceApplyResult }) {
  return (
    <div className="space-y-2 text-sm">
      <p className={result.success ? 'text-success' : 'text-danger'}>
        {result.message}
        {result.default_route_interface && (
          <span className="text-on-surface-muted">
            {' '}
            (default route via {result.default_route_interface})
          </span>
        )}
      </p>
      {result.changes.length === 0 ? (
        <p className="text-on-surface-muted">Host state already matches the desired configuration.</p>
      ) : (
        <ul className="space-y-1">
          {result.changes.map((change, idx) => (
            <li key={idx} className="flex items-start gap-2">
              <Badge variant={change.ok ? 'success' : 'danger'}>{change.ok ? 'ok' : 'failed'}</Badge>
              <span className="text-on-surface-muted">
                <span className="font-medium text-on-surface">{change.interface}</span>{' '}
                [{change.action}] {change.detail}
              </span>
            </li>
          ))}
        </ul>
      )}
      <p className="text-xs text-on-surface-muted">
        {result.netplan_written
          ? `Persisted to ${result.netplan_file} on the host (survives reboot).`
          : 'Not persisted — changes are live-only.'}
      </p>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Interfaces page                                                    */
/* ------------------------------------------------------------------ */

export function Interfaces() {
  const { selectedInstanceId } = useInstanceStore()
  const { data: instances } = useInstances()
  const instance = instances?.find((i) => i.id === selectedInstanceId)
  const instanceName = instance?.name ?? ''
  const { user } = useAuthStore()
  const isAdmin = user?.role === 'admin' || user?.role === 'superadmin'

  const { data: configured, isLoading, isError, refetch } = useNetworkInterfaces(selectedInstanceId ?? 0)
  const {
    data: live,
    refetch: refetchLive,
    isFetching: liveFetching,
  } = useLiveNetworkInterfaces(selectedInstanceId ?? 0)

  const createMutation = useCreateNetworkInterface(selectedInstanceId ?? 0)
  const updateMutation = useUpdateNetworkInterface(selectedInstanceId ?? 0)
  const deleteMutation = useDeleteNetworkInterface(selectedInstanceId ?? 0)
  const applyMutation = useApplyNetworkInterfaces(selectedInstanceId ?? 0)

  const [showCreate, setShowCreate] = useState(false)
  const [editTarget, setEditTarget] = useState<NetworkInterface | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<NetworkInterface | null>(null)
  const [showApplyConfirm, setShowApplyConfirm] = useState(false)
  const [applyForce, setApplyForce] = useState(false)
  const [applyResult, setApplyResult] = useState<InterfaceApplyResult | null>(null)

  const handleCreate = async (data: NetworkInterfaceCreate | NetworkInterfaceUpdate) => {
    try {
      await createMutation.mutateAsync(data as NetworkInterfaceCreate)
      setShowCreate(false)
      toast.success('Interface added')
    } catch (err) {
      toast.error(getErrMsg(err))
    }
  }

  const handleUpdate = async (data: NetworkInterfaceCreate | NetworkInterfaceUpdate) => {
    if (!editTarget) return
    try {
      await updateMutation.mutateAsync({ id: editTarget.id, ...(data as NetworkInterfaceUpdate) })
      setEditTarget(null)
      toast.success('Interface updated')
    } catch (err) {
      toast.error(getErrMsg(err))
    }
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    try {
      await deleteMutation.mutateAsync(deleteTarget.id)
      setDeleteTarget(null)
      toast.success('Interface removed')
    } catch (err) {
      toast.error(getErrMsg(err))
    }
  }

  const handleDiscover = async () => {
    try {
      await refetchLive()
    } catch (err) {
      toast.error(getErrMsg(err))
    }
  }

  const handleApply = async () => {
    try {
      const result = await applyMutation.mutateAsync({ force: applyForce })
      setShowApplyConfirm(false)
      setApplyForce(false)
      if (result.success) {
        toast.success('Configuration applied to host')
      } else {
        toast.error('Apply finished with errors')
      }
      setApplyResult(result)
      void refetchLive()
    } catch (err) {
      setShowApplyConfirm(false)
      toast.error(getErrMsg(err))
    }
  }

  /* ── No instance selected ── */
  if (!selectedInstanceId) {
    return (
      <div>
        <PageHeader title="Interfaces" />
        <Card className="mt-6">
          <div className="flex items-center gap-3 text-on-surface-muted">
            <Info className="h-5 w-5 shrink-0" />
            <p className="text-sm">Select an instance from the top bar to manage its host interfaces.</p>
          </div>
        </Card>
      </div>
    )
  }

  /* ── Configured interfaces table ── */
  const columns = [
    {
      key: 'name',
      header: 'Interface',
      render: (iface: NetworkInterface) => (
        <div>
          <p className="font-medium text-on-surface font-mono">{iface.name}</p>
          {iface.description && (
            <p className="text-xs text-on-surface-muted">{iface.description}</p>
          )}
        </div>
      ),
    },
    {
      key: 'role',
      header: 'Role',
      render: (iface: NetworkInterface) => <Badge variant="neutral">{iface.type}</Badge>,
    },
    {
      key: 'config',
      header: 'Configuration',
      render: (iface: NetworkInterface) =>
        iface.config_type === 'static' ? (
          <div className="text-sm text-on-surface-muted space-y-0.5">
            <span>{iface.ip_address}/{iface.netmask}</span>
            {iface.gateway && <span>GW: {iface.gateway}</span>}
          </div>
        ) : (
          <span className="text-sm text-on-surface-muted">DHCP</span>
        ),
    },
    {
      key: 'mtu',
      header: 'MTU',
      render: (iface: NetworkInterface) => (
        <span className="text-sm text-on-surface-muted">{iface.mtu ?? '-'}</span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (iface: NetworkInterface) => (
        <Badge variant={iface.enabled ? 'success' : 'neutral'}>
          {iface.enabled ? 'Enabled' : 'Disabled'}
        </Badge>
      ),
    },
    ...(isAdmin
      ? [
          {
            key: 'actions',
            header: '',
            render: (iface: NetworkInterface) => (
              <div className="flex items-center gap-2">
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setEditTarget(iface)
                  }}
                  className="text-sm text-primary hover:text-primary-hover"
                >
                  Edit
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setDeleteTarget(iface)
                  }}
                  className="text-sm text-danger hover:text-danger/80"
                >
                  Delete
                </button>
              </div>
            ),
          },
        ]
      : []),
  ]

  const liveByDefault = live?.default_route_interface

  return (
    <div>
      <PageHeader
        title="Interfaces"
        description={
          instanceName
            ? `Host network interface configuration for ${instanceName}`
            : 'Host network interface configuration'
        }
        primaryAction={
          isAdmin ? (
            <Button icon={Plus} onClick={() => setShowCreate(true)}>
              Add Interface
            </Button>
          ) : undefined
        }
        secondaryActions={[
          <Button
            key="apply"
            variant="secondary"
            icon={Upload}
            loading={applyMutation.isPending}
            disabled={!isAdmin}
            onClick={() => setShowApplyConfirm(true)}
          >
            Apply to Host
          </Button>,
        ]}
      />

      {/* ── Desired configuration ── */}
      <div className="mt-6">
        <DataTable
          columns={columns}
          data={configured || []}
          keyExtractor={(iface) => iface.id}
          enableSorting
          isLoading={isLoading}
          isError={isError}
          onRetry={() => refetch()}
          emptyContent={
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Cable className="h-10 w-10 text-on-surface-muted mb-3" />
              <p className="text-sm text-on-surface-muted mb-2">No interfaces configured</p>
              <p className="text-xs text-on-surface-muted mb-4">
                Add the host&apos;s network interfaces to manage their configuration.
              </p>
              {isAdmin && (
                <Button icon={Plus} onClick={() => setShowCreate(true)}>
                  Add Interface
                </Button>
              )}
            </div>
          }
        />
      </div>

      {/* ── Live state ── */}
      <Card
        title="Live Host State"
        className="mt-6"
        actions={
          <Button variant="ghost" icon={ScanSearch} loading={liveFetching} onClick={handleDiscover}>
            Discover
          </Button>
        }
      >
        {!live ? (
          <div className="flex flex-col items-center justify-center py-10 text-center">
            <Download className="h-8 w-8 text-on-surface-muted mb-3" />
            <p className="text-sm text-on-surface-muted mb-1">
              Query the node agent for the host&apos;s current interfaces
            </p>
            <p className="text-xs text-on-surface-muted">
              Requires the node-agent container to run on this host.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {live.interfaces.map((iface) => (
              <div key={iface.name} className="flex items-center justify-between py-3">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-sm font-medium text-on-surface">{iface.name}</span>
                  <Badge variant={iface.up ? 'success' : 'neutral'}>
                    {iface.up ? 'up' : iface.operstate.toLowerCase() || 'down'}
                  </Badge>
                  {iface.has_default_route && <Badge variant="info">default route</Badge>}
                </div>
                <div className="text-sm text-on-surface-muted text-right space-y-0.5">
                  <div>{addrList(iface) || 'no IPv4 address'}</div>
                  <div className="text-xs">
                    MTU {iface.mtu ?? '-'}
                    {liveByDefault === iface.name && live.default_gateway
                      ? ` · GW ${live.default_gateway}`
                      : ''}
                    {iface.mac ? ` · ${iface.mac}` : ''}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* ── Apply result ── */}
      {applyResult && (
        <Card title="Last Apply Result" className="mt-6">
          <ApplyResultCard result={applyResult} />
        </Card>
      )}

      {/* ── Create modal ── */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Add Interface">
        <InterfaceForm
          onSubmit={handleCreate}
          onCancel={() => setShowCreate(false)}
          loading={createMutation.isPending}
        />
      </Modal>

      {/* ── Edit modal ── */}
      <Modal open={!!editTarget} onClose={() => setEditTarget(null)} title="Edit Interface">
        {editTarget && (
          <InterfaceForm
            initial={editTarget}
            onSubmit={handleUpdate}
            onCancel={() => setEditTarget(null)}
            loading={updateMutation.isPending}
          />
        )}
      </Modal>

      {/* ── Delete confirm ── */}
      <ConfirmDialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Delete Interface"
        message={`Remove "${deleteTarget?.name}" from the desired configuration?`}
        impact="The host keeps its current configuration until the next apply."
        loading={deleteMutation.isPending}
      />

      {/* ── Apply confirm ── */}
      <Modal open={showApplyConfirm} onClose={() => setShowApplyConfirm(false)} title="Apply Interface Configuration">
        <div className="space-y-4">
          <p className="text-sm text-on-surface">
            Applies the desired interface configuration to host{' '}
            <span className="font-medium">{instanceName || `#${selectedInstanceId}`}</span> via the
            node agent.
          </p>
          <p className="text-sm text-on-surface-muted">
            Changes take effect immediately and are persisted to the host&apos;s netplan config.
            Changing the interface that carries the default route can interrupt management
            connectivity.
          </p>
          <label className="flex items-start gap-2 text-sm text-on-surface">
            <input
              type="checkbox"
              checked={applyForce}
              onChange={(e) => setApplyForce(e.target.checked)}
              className="mt-0.5"
            />
            <span>
              Allow changes to the interface carrying the default route (may cut management
              connectivity)
            </span>
          </label>
          <div className="flex justify-end gap-3 pt-2">
            <Button
              variant="secondary"
              onClick={() => {
                setShowApplyConfirm(false)
                setApplyForce(false)
              }}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              loading={applyMutation.isPending}
              onClick={handleApply}
            >
              Apply
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
