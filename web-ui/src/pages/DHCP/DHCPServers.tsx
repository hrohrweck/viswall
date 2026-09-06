import { useState } from 'react'
import {
  Activity,
  Info,
  Plus,
  Play,
  RotateCw,
  Square,
  Trash2,
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

import { useInstanceStore } from '../../stores/instance'
import {
  useCreateDHCPOption,
  useCreateDHCPPool,
  useCreateDHCPReservation,
  useCreateDHCPServer,
  useCreateDHCPSubnet,
  useDeleteDHCPOption,
  useDeleteDHCPPool,
  useDeleteDHCPReservation,
  useDeleteDHCPServer,
  useDeleteDHCPSubnet,
  useDHCPActiveLeases,
  useDHCPLeases,
  useDHCPOptions,
  useDHCPPools,
  useDHCPReservations,
  useDHCPServerAction,
  useDHCPServers,
  useDHCPSubnets,
  useReleaseDHCPLease,
} from '../../hooks/useApi'
import {
  Badge,
  Button,
  Card,
  ConfirmDialog,
  DataTable,
  IconButton,
  Modal,
  PageHeader,
  QueryError,
  Skeleton,
  SkeletonText,
  StatusBadge,
  toast,
} from '../../components/ui'
import { DHCPServerForm } from '../../components/forms/DHCPServerForm'
import { DHCPSubnetForm } from '../../components/forms/DHCPSubnetForm'
import { DHCPPoolForm } from '../../components/forms/DHCPPoolForm'
import { DHCPReservationForm } from '../../components/forms/DHCPReservationForm'
import { DHCPOptionForm } from '../../components/forms/DHCPOptionForm'
import type {
  DHCPLease,
  DHCPOption,
  DHCPPool,
  DHCPReservation,
  DHCPServer,
  DHCPSubnet,
} from '../../types'
import { DHCPSubnetType } from '../../types'
import { cn, getErrMsg } from '../../lib/utils'

/* ------------------------------------------------------------------ */
/*  Lookup tables                                                      */
/* ------------------------------------------------------------------ */

type ServerAction = 'start' | 'stop' | 'reload'

const actionVerb: Record<ServerAction, string> = {
  start: 'started',
  stop: 'stopped',
  reload: 'reloaded',
}

const actionLabel: Record<ServerAction, string> = {
  start: 'Start',
  stop: 'Stop',
  reload: 'Reload',
}

const leaseStateVariant: Record<
  string,
  'success' | 'danger' | 'warning' | 'info' | 'neutral'
> = {
  active: 'success',
  released: 'neutral',
  expired: 'warning',
}

/* ------------------------------------------------------------------ */
/*  DHCPServers                                                        */
/* ------------------------------------------------------------------ */

export function DHCPServers() {
  const { selectedInstanceId } = useInstanceStore()

  const [selectedServer, setSelectedServer] = useState<DHCPServer | null>(null)
  const [selectedSubnet, setSelectedSubnet] = useState<DHCPSubnet | null>(null)

  const [createServerOpen, setCreateServerOpen] = useState(false)
  const [createSubnetOpen, setCreateSubnetOpen] = useState(false)
  const [createPoolOpen, setCreatePoolOpen] = useState(false)
  const [createReservationOpen, setCreateReservationOpen] = useState(false)
  const [createOptionOpen, setCreateOptionOpen] = useState(false)

  const [deleteServerTarget, setDeleteServerTarget] = useState<DHCPServer | null>(null)
  const [deleteSubnetTarget, setDeleteSubnetTarget] = useState<DHCPSubnet | null>(null)
  const [deletePoolTarget, setDeletePoolTarget] = useState<DHCPPool | null>(null)
  const [deleteReservationTarget, setDeleteReservationTarget] =
    useState<DHCPReservation | null>(null)
  const [deleteOptionTarget, setDeleteOptionTarget] = useState<DHCPOption | null>(null)
  const [releaseLeaseTarget, setReleaseLeaseTarget] = useState<DHCPLease | null>(null)

  const [actionTarget, setActionTarget] = useState<{
    server: DHCPServer
    action: ServerAction
  } | null>(null)

  const {
    data: servers,
    isLoading: serversLoading,
    isError: serversError,
    refetch: refetchServers,
  } = useDHCPServers(selectedInstanceId || 0)
  const {
    data: subnets,
    isLoading: subnetsLoading,
    isError: subnetsError,
    refetch: refetchSubnets,
  } = useDHCPSubnets(selectedServer?.id || 0)
  const {
    data: pools,
    isLoading: poolsLoading,
    isError: poolsError,
    refetch: refetchPools,
  } = useDHCPPools(selectedSubnet?.id || 0)
  const {
    data: reservations,
    isLoading: reservationsLoading,
    isError: reservationsError,
    refetch: refetchReservations,
  } = useDHCPReservations(selectedSubnet?.id || 0)
  const {
    data: options,
    isLoading: optionsLoading,
    isError: optionsError,
    refetch: refetchOptions,
  } = useDHCPOptions(selectedSubnet?.id || 0)
  const {
    data: leases,
    isLoading: leasesLoading,
    isError: leasesError,
    refetch: refetchLeases,
  } = useDHCPLeases(selectedSubnet?.id || 0)
  const { data: activeLeases } = useDHCPActiveLeases(!!selectedInstanceId)

  const createServerMutation = useCreateDHCPServer(selectedInstanceId || 0)
  const createSubnetMutation = useCreateDHCPSubnet(selectedServer?.id || 0)
  const createPoolMutation = useCreateDHCPPool(selectedSubnet?.id || 0)
  const createReservationMutation = useCreateDHCPReservation(selectedSubnet?.id || 0)
  const createOptionMutation = useCreateDHCPOption(selectedSubnet?.id || 0)

  const deleteServerMutation = useDeleteDHCPServer(selectedInstanceId || 0)
  const deleteSubnetMutation = useDeleteDHCPSubnet(selectedServer?.id || 0)
  const deletePoolMutation = useDeleteDHCPPool(selectedSubnet?.id || 0)
  const deleteReservationMutation = useDeleteDHCPReservation(selectedSubnet?.id || 0)
  const deleteOptionMutation = useDeleteDHCPOption(selectedSubnet?.id || 0)

  const actionMutation = useDHCPServerAction(selectedInstanceId || 0)
  const releaseLeaseMutation = useReleaseDHCPLease(selectedSubnet?.id || 0)

  /* ── No instance selected ── */
  if (!selectedInstanceId) {
    return (
      <div>
        <PageHeader title="DHCP Servers" />
        <Card className="mt-6">
          <div className="flex items-center gap-3 text-on-surface-muted">
            <Info className="h-5 w-5 shrink-0" />
            <p className="text-sm">
              Select an instance from the top bar to manage its DHCP servers.
            </p>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="DHCP Servers"
        description="Address pools, reservations, custom options, and lease control"
        primaryAction={
          <Button onClick={() => setCreateServerOpen(true)}>
            <Plus className="w-4 h-4" />
            New DHCP Server
          </Button>
        }
      />

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        {/* ── Servers pane ─────────────────────────────────────────────── */}
        <Card title="Servers" padding="p-0">
          {serversLoading ? (
            <div className="p-5 space-y-3">
              {Array.from({ length: 3 }, (_, i) => (
                <SkeletonText key={i} lines={2} />
              ))}
            </div>
          ) : serversError ? (
            <div className="p-5">
              <QueryError onRetry={refetchServers} />
            </div>
          ) : servers && servers.length > 0 ? (
            <div className="divide-y divide-border">
              {servers.map((server) => (
                <button
                  key={server.id}
                  type="button"
                  onClick={() => {
                    setSelectedServer(server)
                    setSelectedSubnet(null)
                  }}
                  className={cn(
                    'w-full text-left px-5 py-3 hover:bg-surface-elevated transition-colors',
                    selectedServer?.id === server.id &&
                      'bg-primary/5 border-l-2 border-l-primary',
                  )}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium text-on-surface truncate">
                      {server.name}
                    </span>
                    <StatusBadge status={server.status} />
                  </div>
                  <div className="mt-1 text-xs text-on-surface-muted">
                    {server.subnets_count} subnets ·{' '}
                    {server.dhcpv4_enabled ? 'v4' : ''}
                    {server.dhcpv4_enabled && server.dhcpv6_enabled ? '+' : ''}
                    {server.dhcpv6_enabled ? 'v6' : ''}
                  </div>
                  <div className="mt-2 flex items-center gap-1">
                    <IconButton
                      icon={Play}
                      size="sm"
                      variant="ghost"
                      label="Start server"
                      onClick={(event) => {
                        event.stopPropagation()
                        setActionTarget({ server, action: 'start' })
                      }}
                    />
                    <IconButton
                      icon={Square}
                      size="sm"
                      variant="ghost"
                      label="Stop server"
                      onClick={(event) => {
                        event.stopPropagation()
                        setActionTarget({ server, action: 'stop' })
                      }}
                    />
                    <IconButton
                      icon={RotateCw}
                      size="sm"
                      variant="ghost"
                      label="Reload server"
                      onClick={(event) => {
                        event.stopPropagation()
                        setActionTarget({ server, action: 'reload' })
                      }}
                    />
                    <IconButton
                      icon={Trash2}
                      size="sm"
                      variant="ghost"
                      className="text-danger hover:text-danger"
                      label="Delete server"
                      onClick={(event) => {
                        event.stopPropagation()
                        setDeleteServerTarget(server)
                      }}
                    />
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div className="p-5 text-sm text-on-surface-muted">
              No DHCP servers yet.
            </div>
          )}
        </Card>

        {/* ── Subnets pane ─────────────────────────────────────────────── */}
        <Card
          title="Subnets"
          padding="p-0"
          actions={
            <Button
              size="sm"
              variant="secondary"
              disabled={!selectedServer}
              onClick={() => setCreateSubnetOpen(true)}
            >
              Add
            </Button>
          }
        >
          {subnetsLoading ? (
            <div className="p-5 space-y-3">
              {Array.from({ length: 3 }, (_, i) => (
                <SkeletonText key={i} lines={2} />
              ))}
            </div>
          ) : subnetsError ? (
            <div className="p-5">
              <QueryError onRetry={refetchSubnets} />
            </div>
          ) : subnets && subnets.length > 0 ? (
            <div className="divide-y divide-border max-h-[420px] overflow-y-auto">
              {subnets.map((subnet) => (
                <button
                  key={subnet.id}
                  type="button"
                  onClick={() => setSelectedSubnet(subnet)}
                  className={cn(
                    'w-full text-left px-5 py-3 hover:bg-surface-elevated transition-colors',
                    selectedSubnet?.id === subnet.id &&
                      'bg-primary/5 border-l-2 border-l-primary',
                  )}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium text-on-surface truncate">
                      {subnet.name}
                    </span>
                    <Badge variant="neutral">{subnet.type}</Badge>
                  </div>
                  <div className="mt-1 text-xs text-on-surface-muted break-all font-mono">
                    {subnet.subnet}
                  </div>
                  <div className="mt-1 text-xs text-on-surface-muted">
                    {subnet.pools_count} pools · {subnet.reservations_count} reservations
                  </div>
                  <div className="mt-2 flex items-center gap-2">
                    <IconButton
                      icon={Trash2}
                      size="sm"
                      variant="ghost"
                      className="text-danger hover:text-danger"
                      label="Delete subnet"
                      onClick={(event) => {
                        event.stopPropagation()
                        setDeleteSubnetTarget(subnet)
                      }}
                    />
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div className="p-5 text-sm text-on-surface-muted">
              {selectedServer ? 'No subnets for this server.' : 'Select a server to view subnets.'}
            </div>
          )}
        </Card>

        {/* ── Pools / Reservations / Options pane ───────────────────────── */}
        <Card
          title="Pools & Reservations"
          padding="p-0"
          actions={
            <>
              <Button
                size="sm"
                variant="secondary"
                disabled={!selectedSubnet}
                onClick={() => setCreatePoolOpen(true)}
              >
                Pool
              </Button>
              <Button
                size="sm"
                variant="secondary"
                disabled={!selectedSubnet}
                onClick={() => setCreateReservationOpen(true)}
              >
                Reservation
              </Button>
            </>
          }
        >
          <div className="max-h-[480px] overflow-y-auto">
            {/* Pools */}
            <div className="px-5 py-2 text-xs font-semibold uppercase text-on-surface-muted">
              Pools
            </div>
            {poolsLoading ? (
              <div className="px-5 pb-3 space-y-2">
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-2/3" />
              </div>
            ) : poolsError ? (
              <div className="px-5 pb-3">
                <QueryError onRetry={refetchPools} />
              </div>
            ) : pools && pools.length > 0 ? (
              <div className="divide-y divide-border">
                {pools.map((pool) => (
                  <div
                    key={pool.id}
                    className="px-5 py-3 flex items-center justify-between gap-2"
                  >
                    <span className="text-sm font-mono text-on-surface break-all">
                      {pool.start_address} - {pool.end_address}
                    </span>
                    <IconButton
                      icon={Trash2}
                      size="sm"
                      variant="ghost"
                      className="text-danger hover:text-danger"
                      label="Delete pool"
                      onClick={() => setDeletePoolTarget(pool)}
                    />
                  </div>
                ))}
              </div>
            ) : (
              <div className="px-5 pb-3 text-sm text-on-surface-muted">
                No pools configured.
              </div>
            )}

            {/* Reservations */}
            <div className="px-5 py-2 mt-2 text-xs font-semibold uppercase text-on-surface-muted border-t border-border">
              Reservations
            </div>
            {reservationsLoading ? (
              <div className="px-5 pb-3 space-y-2">
                <Skeleton className="h-8 w-full" />
              </div>
            ) : reservationsError ? (
              <div className="px-5 pb-3">
                <QueryError onRetry={refetchReservations} />
              </div>
            ) : reservations && reservations.length > 0 ? (
              <div className="divide-y divide-border">
                {reservations.map((reservation) => (
                  <div
                    key={reservation.id}
                    className="px-5 py-3 flex items-center justify-between gap-2"
                  >
                    <div className="min-w-0">
                      <div className="text-sm font-mono text-on-surface break-all">
                        {reservation.ip_address}
                      </div>
                      <div className="text-xs text-on-surface-muted break-all font-mono">
                        {reservation.hw_address}
                      </div>
                    </div>
                    <IconButton
                      icon={Trash2}
                      size="sm"
                      variant="ghost"
                      className="text-danger hover:text-danger"
                      label="Delete reservation"
                      onClick={() => setDeleteReservationTarget(reservation)}
                    />
                  </div>
                ))}
              </div>
            ) : (
              <div className="px-5 pb-3 text-sm text-on-surface-muted">
                No reservations configured.
              </div>
            )}

            {/* Options */}
            <div className="px-5 py-2 mt-2 text-xs font-semibold uppercase text-on-surface-muted border-t border-border flex items-center justify-between">
              <span>Options</span>
              <Button
                size="sm"
                variant="secondary"
                disabled={!selectedSubnet}
                onClick={() => setCreateOptionOpen(true)}
              >
                Add
              </Button>
            </div>
            {optionsLoading ? (
              <div className="px-5 pb-3 space-y-2">
                <Skeleton className="h-8 w-full" />
              </div>
            ) : optionsError ? (
              <div className="px-5 pb-3">
                <QueryError onRetry={refetchOptions} />
              </div>
            ) : options && options.length > 0 ? (
              <div className="divide-y divide-border">
                {options.map((option) => (
                  <div
                    key={option.id}
                    className="px-5 py-3 flex items-center justify-between gap-2"
                  >
                    <div className="min-w-0">
                      <div className="text-sm font-medium text-on-surface">
                        {option.option_name} ({option.option_code})
                      </div>
                      <div className="text-xs text-on-surface-muted break-all font-mono">
                        {option.option_value}
                      </div>
                    </div>
                    <IconButton
                      icon={Trash2}
                      size="sm"
                      variant="ghost"
                      className="text-danger hover:text-danger"
                      label="Delete option"
                      onClick={() => setDeleteOptionTarget(option)}
                    />
                  </div>
                ))}
              </div>
            ) : (
              <div className="px-5 pb-3 text-sm text-on-surface-muted">
                No custom options configured.
              </div>
            )}
          </div>
        </Card>

        {/* ── Leases pane (DataTable) ──────────────────────────────────── */}
        <Card title="Leases" padding="p-0">
          <DataTable
            columns={[
              {
                key: 'ip_address',
                header: 'Address',
                className: 'font-mono',
                render: (lease: DHCPLease) => (
                  <span className="font-mono text-sm">{lease.ip_address}</span>
                ),
              },
              {
                key: 'hw_address',
                header: 'MAC',
                className: 'font-mono',
                render: (lease: DHCPLease) => (
                  <span className="font-mono text-sm text-on-surface-muted">
                    {lease.hw_address ?? '—'}
                  </span>
                ),
              },
              {
                key: 'state',
                header: 'State',
                render: (lease: DHCPLease) => (
                  <Badge variant={leaseStateVariant[lease.state] ?? 'neutral'}>
                    {lease.state}
                  </Badge>
                ),
              },
              {
                key: 'lease_end',
                header: 'Expires',
                render: (lease: DHCPLease) =>
                  lease.lease_end
                    ? formatDistanceToNow(new Date(lease.lease_end), { addSuffix: true })
                    : '—',
              },
            ]}
            data={leases || []}
            keyExtractor={(lease) => lease.id}
            searchable
            searchPlaceholder="Search leases…"
            isLoading={leasesLoading}
            isError={leasesError}
            onRetry={() => refetchLeases()}
            rowActions={(lease) =>
              lease.state === 'active' ? (
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={() => setReleaseLeaseTarget(lease)}
                >
                  Release
                </Button>
              ) : null
            }
            emptyContent={
              <div className="p-5 text-sm text-on-surface-muted">
                {selectedSubnet ? 'No leases for this subnet.' : 'Select a subnet to view leases.'}
              </div>
            }
          />
          <div className="px-5 py-3 border-t border-border text-xs text-on-surface-muted">
            Active leases on instance: {activeLeases?.length ?? 0}
          </div>
        </Card>
      </div>

      {/* ── Create Server modal ──────────────────────────────────────── */}
      <Modal
        open={createServerOpen}
        onClose={() => setCreateServerOpen(false)}
        title="Create DHCP Server"
      >
        <DHCPServerForm
          loading={createServerMutation.isPending}
          onSubmit={(payload) => {
            createServerMutation.mutate(payload, {
              onSuccess: () => {
                toast.success('DHCP server created')
                setCreateServerOpen(false)
              },
              onError: (e) => toast.error(getErrMsg(e)),
            })
          }}
        />
      </Modal>

      {/* ── Create Subnet modal ───────────────────────────────────────── */}
      <Modal
        open={createSubnetOpen}
        onClose={() => setCreateSubnetOpen(false)}
        title="Create Subnet"
      >
        <DHCPSubnetForm
          loading={createSubnetMutation.isPending}
          onSubmit={(payload) => {
            createSubnetMutation.mutate(payload, {
              onSuccess: () => {
                toast.success('Subnet created')
                setCreateSubnetOpen(false)
              },
              onError: (e) => toast.error(getErrMsg(e)),
            })
          }}
        />
      </Modal>

      {/* ── Create Pool modal ─────────────────────────────────────────── */}
      <Modal
        open={createPoolOpen}
        onClose={() => setCreatePoolOpen(false)}
        title="Create Pool"
      >
        <DHCPPoolForm
          subnetType={selectedSubnet?.type || DHCPSubnetType.V4}
          loading={createPoolMutation.isPending}
          onSubmit={(payload) => {
            createPoolMutation.mutate(payload, {
              onSuccess: () => {
                toast.success('Pool created')
                setCreatePoolOpen(false)
              },
              onError: (e) => toast.error(getErrMsg(e)),
            })
          }}
        />
      </Modal>

      {/* ── Create Reservation modal ──────────────────────────────────── */}
      <Modal
        open={createReservationOpen}
        onClose={() => setCreateReservationOpen(false)}
        title="Create Reservation"
      >
        <DHCPReservationForm
          subnetType={selectedSubnet?.type || DHCPSubnetType.V4}
          loading={createReservationMutation.isPending}
          onSubmit={(payload) => {
            createReservationMutation.mutate(payload, {
              onSuccess: () => {
                toast.success('Reservation created')
                setCreateReservationOpen(false)
              },
              onError: (e) => toast.error(getErrMsg(e)),
            })
          }}
        />
      </Modal>

      {/* ── Create Option modal ───────────────────────────────────────── */}
      <Modal
        open={createOptionOpen}
        onClose={() => setCreateOptionOpen(false)}
        title="Create DHCP Option"
      >
        <DHCPOptionForm
          subnetType={selectedSubnet?.type || DHCPSubnetType.V4}
          loading={createOptionMutation.isPending}
          onSubmit={(payload) => {
            createOptionMutation.mutate(payload, {
              onSuccess: () => {
                toast.success('DHCP option created')
                setCreateOptionOpen(false)
              },
              onError: (e) => toast.error(getErrMsg(e)),
            })
          }}
        />
      </Modal>

      {/* ── Server action ConfirmDialog (Start/Stop/Reload) ───────────── */}
      <ConfirmDialog
        open={!!actionTarget}
        onClose={() => setActionTarget(null)}
        variant={actionTarget?.action === 'stop' ? 'danger' : 'warning'}
        confirmLabel={actionTarget ? actionLabel[actionTarget.action] : 'Confirm'}
        title={`${actionTarget ? actionLabel[actionTarget.action] : ''} DHCP Server`}
        message={`${actionTarget ? actionLabel[actionTarget.action] : ''} ${
          actionTarget?.server.name
        }?`}
        impact={
          actionTarget?.action === 'stop'
            ? 'Stopping the server will stop serving addresses until it is restarted.'
            : actionTarget?.action === 'reload'
              ? 'Reloading applies pending configuration changes without dropping active leases.'
              : undefined
        }
        loading={actionMutation.isPending}
        onConfirm={() => {
          if (!actionTarget) return
          const { server, action } = actionTarget
          actionMutation.mutate(
            { serverId: server.id, action },
            {
              onSuccess: () => {
                toast.success(`Server ${actionVerb[action]}`)
                setActionTarget(null)
              },
              onError: (e) => toast.error(getErrMsg(e)),
            },
          )
        }}
      />

      {/* ── Delete Server ConfirmDialog ───────────────────────────────── */}
      <ConfirmDialog
        open={!!deleteServerTarget}
        onClose={() => setDeleteServerTarget(null)}
        title="Delete DHCP Server"
        message={`Delete ${deleteServerTarget?.name}?`}
        impact="This will remove all associated subnets and leases."
        loading={deleteServerMutation.isPending}
        onConfirm={() => {
          if (!deleteServerTarget) return
          deleteServerMutation.mutate(deleteServerTarget.id, {
            onSuccess: () => {
              if (selectedServer?.id === deleteServerTarget.id) {
                setSelectedServer(null)
                setSelectedSubnet(null)
              }
              toast.success('DHCP server deleted')
              setDeleteServerTarget(null)
            },
            onError: (e) => toast.error(getErrMsg(e)),
          })
        }}
      />

      {/* ── Delete Subnet ConfirmDialog ───────────────────────────────── */}
      <ConfirmDialog
        open={!!deleteSubnetTarget}
        onClose={() => setDeleteSubnetTarget(null)}
        title="Delete Subnet"
        message={`Delete subnet ${deleteSubnetTarget?.subnet}?`}
        loading={deleteSubnetMutation.isPending}
        onConfirm={() => {
          if (!deleteSubnetTarget) return
          deleteSubnetMutation.mutate(deleteSubnetTarget.id, {
            onSuccess: () => {
              if (selectedSubnet?.id === deleteSubnetTarget.id) {
                setSelectedSubnet(null)
              }
              toast.success('Subnet deleted')
              setDeleteSubnetTarget(null)
            },
            onError: (e) => toast.error(getErrMsg(e)),
          })
        }}
      />

      {/* ── Delete Pool ConfirmDialog ─────────────────────────────────── */}
      <ConfirmDialog
        open={!!deletePoolTarget}
        onClose={() => setDeletePoolTarget(null)}
        title="Delete Pool"
        message={`Delete pool ${deletePoolTarget?.start_address} - ${deletePoolTarget?.end_address}?`}
        loading={deletePoolMutation.isPending}
        onConfirm={() => {
          if (!deletePoolTarget) return
          deletePoolMutation.mutate(deletePoolTarget.id, {
            onSuccess: () => {
              toast.success('Pool deleted')
              setDeletePoolTarget(null)
            },
            onError: (e) => toast.error(getErrMsg(e)),
          })
        }}
      />

      {/* ── Delete Reservation ConfirmDialog ──────────────────────────── */}
      <ConfirmDialog
        open={!!deleteReservationTarget}
        onClose={() => setDeleteReservationTarget(null)}
        title="Delete Reservation"
        message={`Delete reservation for ${deleteReservationTarget?.ip_address}?`}
        loading={deleteReservationMutation.isPending}
        onConfirm={() => {
          if (!deleteReservationTarget) return
          deleteReservationMutation.mutate(deleteReservationTarget.id, {
            onSuccess: () => {
              toast.success('Reservation deleted')
              setDeleteReservationTarget(null)
            },
            onError: (e) => toast.error(getErrMsg(e)),
          })
        }}
      />

      {/* ── Delete Option ConfirmDialog ───────────────────────────────── */}
      <ConfirmDialog
        open={!!deleteOptionTarget}
        onClose={() => setDeleteOptionTarget(null)}
        title="Delete DHCP Option"
        message={`Delete option ${deleteOptionTarget?.option_name} (${deleteOptionTarget?.option_code})?`}
        loading={deleteOptionMutation.isPending}
        onConfirm={() => {
          if (!deleteOptionTarget) return
          deleteOptionMutation.mutate(deleteOptionTarget.id, {
            onSuccess: () => {
              toast.success('DHCP option deleted')
              setDeleteOptionTarget(null)
            },
            onError: (e) => toast.error(getErrMsg(e)),
          })
        }}
      />

      {/* ── Release Lease ConfirmDialog ───────────────────────────────── */}
      <ConfirmDialog
        open={!!releaseLeaseTarget}
        onClose={() => setReleaseLeaseTarget(null)}
        title="Release Lease"
        message={`Release active lease ${releaseLeaseTarget?.ip_address}?`}
        impact={`Releases lease ${releaseLeaseTarget?.ip_address}; the client must re-request an IP address.`}
        confirmLabel="Release"
        variant="danger"
        loading={releaseLeaseMutation.isPending}
        onConfirm={() => {
          if (!releaseLeaseTarget) return
          releaseLeaseMutation.mutate(releaseLeaseTarget.id, {
            onSuccess: () => {
              toast.success('Lease released')
              setReleaseLeaseTarget(null)
            },
            onError: (e) => toast.error(getErrMsg(e)),
          })
        }}
      />
    </div>
  )
}
