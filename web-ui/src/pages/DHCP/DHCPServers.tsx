import { useMemo, useState } from 'react'
import { Activity, Play, Plus, RotateCw, Server, Square, Trash2 } from 'lucide-react'

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
  ConfirmDialog,
  EmptyState,
  InstanceSelector,
  LoadingSpinner,
  Modal,
  StatusBadge,
} from '../../components/ui'
import type {
  DHCPOption,
  DHCPOptionCreate,
  DHCPPool,
  DHCPPoolCreate,
  DHCPReservation,
  DHCPReservationCreate,
  DHCPServer,
  DHCPServerCreate,
  DHCPSubnet,
  DHCPSubnetCreate,
  DHCPLease,
} from '../../types'
import { DHCPHAMode, DHCPSubnetType } from '../../types'

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
  const [deleteReservationTarget, setDeleteReservationTarget] = useState<DHCPReservation | null>(null)
  const [deleteOptionTarget, setDeleteOptionTarget] = useState<DHCPOption | null>(null)
  const [releaseLeaseTarget, setReleaseLeaseTarget] = useState<DHCPLease | null>(null)

  const { data: servers, isLoading: serversLoading } = useDHCPServers(selectedInstanceId || 0)
  const { data: subnets, isLoading: subnetsLoading } = useDHCPSubnets(selectedServer?.id || 0)
  const { data: pools, isLoading: poolsLoading } = useDHCPPools(selectedSubnet?.id || 0)
  const { data: reservations, isLoading: reservationsLoading } = useDHCPReservations(selectedSubnet?.id || 0)
  const { data: options, isLoading: optionsLoading } = useDHCPOptions(selectedSubnet?.id || 0)
  const { data: leases, isLoading: leasesLoading } = useDHCPLeases(selectedSubnet?.id || 0)
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

  const selectedServerFromList = useMemo(() => {
    if (!servers || !selectedServer) return null
    return servers.find((item) => item.id === selectedServer.id) || null
  }, [servers, selectedServer])

  if (!selectedInstanceId) {
    return (
      <div>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">DHCP Servers</h2>
            <p className="text-gray-600 dark:text-gray-400 mt-1">Manage Kea DHCPv4/DHCPv6 servers, pools, and leases</p>
          </div>
        </div>
        <EmptyState icon={Server} title="Select an Instance" description="Choose an instance to manage DHCP." />
        <div className="mt-4"><InstanceSelector /></div>
      </div>
    )
  }

  if (serversLoading) return <LoadingSpinner />

  return (
    <div>
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between mb-6">
        <div className="flex items-center gap-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">DHCP Servers</h2>
            <p className="text-gray-600 dark:text-gray-400 mt-1">Address pools, reservations, custom options, and lease control</p>
          </div>
          <InstanceSelector />
        </div>
        <button
          onClick={() => setCreateServerOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          <Plus className="w-5 h-5" />
          New DHCP Server
        </button>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 dark:bg-gray-900 dark:border-gray-700">
          <div className="px-4 py-3 border-b border-gray-200 font-semibold dark:border-gray-700 dark:text-white">Servers</div>
          <div className="divide-y divide-gray-100 dark:divide-gray-800">
            {servers && servers.length > 0 ? servers.map((server) => (
              <button
                key={server.id}
                onClick={() => {
                  setSelectedServer(server)
                  setSelectedSubnet(null)
                }}
                className={`w-full text-left px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800 ${selectedServer?.id === server.id ? 'bg-primary-50 dark:bg-primary-950/30' : ''}`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium text-gray-900 truncate dark:text-white">{server.name}</span>
                  <StatusBadge status={server.status} />
                </div>
                <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  {server.subnets_count} subnets · {server.dhcpv4_enabled ? 'v4' : ''}{server.dhcpv4_enabled && server.dhcpv6_enabled ? '+' : ''}{server.dhcpv6_enabled ? 'v6' : ''}
                </div>
                <div className="mt-2 flex items-center gap-2">
                  <button
                    onClick={(event) => {
                      event.stopPropagation()
                      void actionMutation.mutateAsync({ serverId: server.id, action: 'start' })
                    }}
                    className="p-1 rounded text-green-700 hover:bg-green-100 dark:text-green-400 dark:hover:bg-green-950/30"
                    title="Start"
                  >
                    <Play className="w-4 h-4" />
                  </button>
                  <button
                    onClick={(event) => {
                      event.stopPropagation()
                      void actionMutation.mutateAsync({ serverId: server.id, action: 'stop' })
                    }}
                    className="p-1 rounded text-gray-700 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
                    title="Stop"
                  >
                    <Square className="w-4 h-4" />
                  </button>
                  <button
                    onClick={(event) => {
                      event.stopPropagation()
                      void actionMutation.mutateAsync({ serverId: server.id, action: 'reload' })
                    }}
                    className="p-1 rounded text-blue-700 hover:bg-blue-100 dark:text-blue-400 dark:hover:bg-blue-950/30"
                    title="Reload"
                  >
                    <RotateCw className="w-4 h-4" />
                  </button>
                  <button
                    onClick={(event) => {
                      event.stopPropagation()
                      setDeleteServerTarget(server)
                    }}
                    className="p-1 rounded text-red-700 hover:bg-red-100 dark:text-red-400 dark:hover:bg-red-950/30"
                    title="Delete"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </button>
            )) : (
              <div className="p-4 text-sm text-gray-500 dark:text-gray-400">No DHCP servers yet.</div>
            )}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 dark:bg-gray-900 dark:border-gray-700">
          <div className="px-4 py-3 border-b border-gray-200 font-semibold flex items-center justify-between dark:border-gray-700 dark:text-white">
            <span>Subnets</span>
            <button
              disabled={!selectedServer}
              onClick={() => setCreateSubnetOpen(true)}
              className="text-sm px-2 py-1 rounded bg-primary-600 text-white disabled:opacity-40"
            >
              Add
            </button>
          </div>
          {subnetsLoading ? <div className="p-4"><LoadingSpinner /></div> : (
            <div className="divide-y divide-gray-100 dark:divide-gray-800">
              {subnets && subnets.length > 0 ? subnets.map((subnet) => (
                <button
                  key={subnet.id}
                  onClick={() => setSelectedSubnet(subnet)}
                  className={`w-full text-left px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800 ${selectedSubnet?.id === subnet.id ? 'bg-primary-50 dark:bg-primary-950/30' : ''}`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium text-gray-900 truncate dark:text-white">{subnet.name}</span>
                    <span className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-700 uppercase dark:bg-gray-800 dark:text-gray-300">{subnet.type}</span>
                  </div>
                  <div className="mt-1 text-xs text-gray-500 break-all dark:text-gray-400">{subnet.subnet}</div>
                  <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">{subnet.pools_count} pools · {subnet.reservations_count} reservations</div>
                  <div className="mt-2 flex items-center gap-2">
                    <button
                      onClick={(event) => {
                        event.stopPropagation()
                        setDeleteSubnetTarget(subnet)
                      }}
                      className="p-1 rounded text-red-700 hover:bg-red-100 dark:text-red-400 dark:hover:bg-red-950/30"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </button>
              )) : (
                <div className="p-4 text-sm text-gray-500 dark:text-gray-400">No subnets for this server.</div>
              )}
            </div>
          )}
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 dark:bg-gray-900 dark:border-gray-700">
          <div className="px-4 py-3 border-b border-gray-200 font-semibold flex items-center justify-between dark:border-gray-700 dark:text-white">
            <span>Pools/Reservations</span>
            <div className="flex gap-2">
              <button
                disabled={!selectedSubnet}
                onClick={() => setCreatePoolOpen(true)}
                className="text-xs px-2 py-1 rounded bg-primary-600 text-white disabled:opacity-40"
              >
                Pool
              </button>
              <button
                disabled={!selectedSubnet}
                onClick={() => setCreateReservationOpen(true)}
                className="text-xs px-2 py-1 rounded bg-emerald-600 text-white disabled:opacity-40"
              >
                Reservation
              </button>
            </div>
          </div>
          <div className="max-h-[480px] overflow-y-auto">
            <div className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase dark:text-gray-400">Pools</div>
            {poolsLoading ? <div className="px-4 pb-3"><LoadingSpinner /></div> : (
              <div className="divide-y divide-gray-100 dark:divide-gray-800">
                {pools && pools.length > 0 ? pools.map((pool) => (
                  <div key={pool.id} className="px-4 py-3">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-medium text-gray-900 break-all dark:text-white">{pool.start_address} - {pool.end_address}</span>
                      <button
                        onClick={() => setDeletePoolTarget(pool)}
                        className="p-1 rounded text-red-700 hover:bg-red-100 dark:text-red-400 dark:hover:bg-red-950/30"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                )) : <div className="px-4 pb-3 text-sm text-gray-500 dark:text-gray-400">No pools configured.</div>}
              </div>
            )}

            <div className="px-4 py-2 mt-2 text-xs font-semibold text-gray-500 uppercase border-t border-gray-100 dark:text-gray-400 dark:border-gray-800">Reservations</div>
            {reservationsLoading ? <div className="px-4 pb-3"><LoadingSpinner /></div> : (
              <div className="divide-y divide-gray-100 dark:divide-gray-800">
                {reservations && reservations.length > 0 ? reservations.map((reservation) => (
                  <div key={reservation.id} className="px-4 py-3">
                    <div className="flex items-center justify-between gap-2">
                      <div>
                        <div className="text-sm font-medium text-gray-900 break-all dark:text-white">{reservation.ip_address}</div>
                        <div className="text-xs text-gray-500 break-all dark:text-gray-400">{reservation.hw_address}</div>
                      </div>
                      <button
                        onClick={() => setDeleteReservationTarget(reservation)}
                        className="p-1 rounded text-red-700 hover:bg-red-100 dark:text-red-400 dark:hover:bg-red-950/30"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                )) : <div className="px-4 pb-3 text-sm text-gray-500 dark:text-gray-400">No reservations configured.</div>}
              </div>
            )}

            <div className="px-4 py-2 mt-2 text-xs font-semibold text-gray-500 uppercase border-t border-gray-100 flex items-center justify-between dark:text-gray-400 dark:border-gray-800">
              <span>Options</span>
              <button
                disabled={!selectedSubnet}
                onClick={() => setCreateOptionOpen(true)}
                className="text-xs px-2 py-1 rounded bg-violet-600 text-white disabled:opacity-40"
              >
                Add
              </button>
            </div>
            {optionsLoading ? <div className="px-4 pb-3"><LoadingSpinner /></div> : (
              <div className="divide-y divide-gray-100 dark:divide-gray-800">
                {options && options.length > 0 ? options.map((option) => (
                  <div key={option.id} className="px-4 py-3">
                    <div className="flex items-center justify-between gap-2">
                      <div>
                        <div className="text-sm font-medium text-gray-900 dark:text-white">{option.option_name} ({option.option_code})</div>
                        <div className="text-xs text-gray-500 break-all dark:text-gray-400">{option.option_value}</div>
                      </div>
                      <button
                        onClick={() => setDeleteOptionTarget(option)}
                        className="p-1 rounded text-red-700 hover:bg-red-100 dark:text-red-400 dark:hover:bg-red-950/30"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                )) : <div className="px-4 pb-3 text-sm text-gray-500 dark:text-gray-400">No custom options configured.</div>}
              </div>
            )}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 dark:bg-gray-900 dark:border-gray-700">
          <div className="px-4 py-3 border-b border-gray-200 font-semibold flex items-center gap-2 dark:border-gray-700 dark:text-white">
            <Activity className="w-4 h-4" />
            Leases
          </div>
          <div className="max-h-[480px] overflow-y-auto divide-y divide-gray-100 dark:divide-gray-800">
            {leasesLoading ? <div className="p-4"><LoadingSpinner /></div> : (
              leases && leases.length > 0 ? leases.map((lease) => (
                <div key={lease.id} className="px-4 py-3">
                  <div className="flex items-center justify-between gap-2">
                    <div>
                      <div className="text-sm font-medium text-gray-900 break-all dark:text-white">{lease.ip_address}</div>
                      <div className="text-xs text-gray-500 break-all dark:text-gray-400">{lease.hostname || lease.hw_address || lease.client_id || 'n/a'}</div>
                    </div>
                    <span className={`text-xs px-2 py-0.5 rounded ${lease.state === 'active' ? 'bg-green-100 text-green-700 dark:bg-green-950/30 dark:text-green-400' : lease.state === 'released' ? 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400' : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-950/30 dark:text-yellow-400'}`}>
                      {lease.state}
                    </span>
                  </div>
                  {lease.state === 'active' ? (
                    <button
                      onClick={() => setReleaseLeaseTarget(lease)}
                      className="mt-2 text-xs px-2 py-1 rounded bg-amber-100 text-amber-800 hover:bg-amber-200 dark:bg-amber-950/30 dark:text-amber-400 dark:hover:bg-amber-900/40"
                    >
                      Release lease
                    </button>
                  ) : null}
                </div>
              )) : <div className="p-4 text-sm text-gray-500 dark:text-gray-400">No leases for this subnet.</div>
            )}
          </div>
          <div className="px-4 py-3 border-t border-gray-200 text-xs text-gray-500 dark:border-gray-800 dark:text-gray-400">
            Active leases on instance: {activeLeases?.length || 0}
          </div>
        </div>
      </div>

      <Modal open={createServerOpen} onClose={() => setCreateServerOpen(false)} title="Create DHCP Server">
        <DHCPServerForm
          loading={createServerMutation.isPending}
          onSubmit={async (payload) => {
            await createServerMutation.mutateAsync(payload)
            setCreateServerOpen(false)
          }}
        />
      </Modal>

      <Modal open={createSubnetOpen} onClose={() => setCreateSubnetOpen(false)} title="Create Subnet">
        <DHCPSubnetForm
          loading={createSubnetMutation.isPending}
          onSubmit={async (payload) => {
            await createSubnetMutation.mutateAsync(payload)
            setCreateSubnetOpen(false)
          }}
        />
      </Modal>

      <Modal open={createPoolOpen} onClose={() => setCreatePoolOpen(false)} title="Create Pool">
        <DHCPPoolForm
          subnetType={selectedSubnet?.type || DHCPSubnetType.V4}
          loading={createPoolMutation.isPending}
          onSubmit={async (payload) => {
            await createPoolMutation.mutateAsync(payload)
            setCreatePoolOpen(false)
          }}
        />
      </Modal>

      <Modal open={createReservationOpen} onClose={() => setCreateReservationOpen(false)} title="Create Reservation">
        <DHCPReservationForm
          subnetType={selectedSubnet?.type || DHCPSubnetType.V4}
          loading={createReservationMutation.isPending}
          onSubmit={async (payload) => {
            await createReservationMutation.mutateAsync(payload)
            setCreateReservationOpen(false)
          }}
        />
      </Modal>

      <Modal open={createOptionOpen} onClose={() => setCreateOptionOpen(false)} title="Create DHCP Option">
        <DHCPOptionForm
          subnetType={selectedSubnet?.type || DHCPSubnetType.V4}
          loading={createOptionMutation.isPending}
          onSubmit={async (payload) => {
            await createOptionMutation.mutateAsync(payload)
            setCreateOptionOpen(false)
          }}
        />
      </Modal>

      <ConfirmDialog
        open={!!deleteServerTarget}
        onClose={() => setDeleteServerTarget(null)}
        onConfirm={() => {
          if (!deleteServerTarget) return
          void deleteServerMutation.mutateAsync(deleteServerTarget.id).then(() => {
            if (selectedServerFromList?.id === deleteServerTarget.id) {
              setSelectedServer(null)
              setSelectedSubnet(null)
            }
            setDeleteServerTarget(null)
          })
        }}
        title="Delete DHCP Server"
        message={`Delete ${deleteServerTarget?.name}? This will remove all associated subnets and leases.`}
        loading={deleteServerMutation.isPending}
      />

      <ConfirmDialog
        open={!!deleteSubnetTarget}
        onClose={() => setDeleteSubnetTarget(null)}
        onConfirm={() => {
          if (!deleteSubnetTarget) return
          void deleteSubnetMutation.mutateAsync(deleteSubnetTarget.id).then(() => {
            if (selectedSubnet?.id === deleteSubnetTarget.id) {
              setSelectedSubnet(null)
            }
            setDeleteSubnetTarget(null)
          })
        }}
        title="Delete Subnet"
        message={`Delete subnet ${deleteSubnetTarget?.subnet}?`}
        loading={deleteSubnetMutation.isPending}
      />

      <ConfirmDialog
        open={!!deletePoolTarget}
        onClose={() => setDeletePoolTarget(null)}
        onConfirm={() => {
          if (!deletePoolTarget) return
          void deletePoolMutation.mutateAsync(deletePoolTarget.id).then(() => setDeletePoolTarget(null))
        }}
        title="Delete Pool"
        message={`Delete pool ${deletePoolTarget?.start_address} - ${deletePoolTarget?.end_address}?`}
        loading={deletePoolMutation.isPending}
      />

      <ConfirmDialog
        open={!!deleteReservationTarget}
        onClose={() => setDeleteReservationTarget(null)}
        onConfirm={() => {
          if (!deleteReservationTarget) return
          void deleteReservationMutation.mutateAsync(deleteReservationTarget.id).then(() => setDeleteReservationTarget(null))
        }}
        title="Delete Reservation"
        message={`Delete reservation for ${deleteReservationTarget?.ip_address}?`}
        loading={deleteReservationMutation.isPending}
      />

      <ConfirmDialog
        open={!!deleteOptionTarget}
        onClose={() => setDeleteOptionTarget(null)}
        onConfirm={() => {
          if (!deleteOptionTarget) return
          void deleteOptionMutation.mutateAsync(deleteOptionTarget.id).then(() => setDeleteOptionTarget(null))
        }}
        title="Delete DHCP Option"
        message={`Delete option ${deleteOptionTarget?.option_name} (${deleteOptionTarget?.option_code})?`}
        loading={deleteOptionMutation.isPending}
      />

      <ConfirmDialog
        open={!!releaseLeaseTarget}
        onClose={() => setReleaseLeaseTarget(null)}
        onConfirm={() => {
          if (!releaseLeaseTarget) return
          void releaseLeaseMutation.mutateAsync(releaseLeaseTarget.id).then(() => setReleaseLeaseTarget(null))
        }}
        title="Release Lease"
        message={`Release active lease ${releaseLeaseTarget?.ip_address}?`}
        loading={releaseLeaseMutation.isPending}
      />
    </div>
  )
}

function DHCPServerForm({
  loading,
  onSubmit,
}: {
  loading: boolean
  onSubmit: (payload: DHCPServerCreate) => Promise<void>
}) {
  const [name, setName] = useState('kea-dhcp-1')
  const [dhcpv4Enabled, setDhcpv4Enabled] = useState(true)
  const [dhcpv6Enabled, setDhcpv6Enabled] = useState(false)
  const [haEnabled, setHaEnabled] = useState(false)
  const [haMode, setHaMode] = useState(DHCPHAMode.HOT_STANDBY)
  const [haPeerAddress, setHaPeerAddress] = useState('')

  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault()
        void onSubmit({
          name,
          dhcpv4_enabled: dhcpv4Enabled,
          dhcpv6_enabled: dhcpv6Enabled,
          ha_enabled: haEnabled,
          ha_mode: haMode,
          ha_peer_address: haEnabled ? haPeerAddress : undefined,
        })
      }}
    >
      <label className="block">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Name</span>
        <input value={name} onChange={(event) => setName(event.target.value)} className="mt-1 w-full border rounded-lg px-3 py-2 dark:bg-gray-800 dark:border-gray-600 dark:text-white" />
      </label>
      <div className="flex items-center gap-6 text-sm dark:text-gray-300">
        <label className="inline-flex items-center gap-2">
          <input type="checkbox" checked={dhcpv4Enabled} onChange={(event) => setDhcpv4Enabled(event.target.checked)} />
          DHCPv4
        </label>
        <label className="inline-flex items-center gap-2">
          <input type="checkbox" checked={dhcpv6Enabled} onChange={(event) => setDhcpv6Enabled(event.target.checked)} />
          DHCPv6
        </label>
      </div>
      <label className="inline-flex items-center gap-2 text-sm dark:text-gray-300">
        <input type="checkbox" checked={haEnabled} onChange={(event) => setHaEnabled(event.target.checked)} />
        Enable HA
      </label>
      {haEnabled ? (
        <>
          <label className="block">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">HA Mode</span>
            <select value={haMode} onChange={(event) => setHaMode(event.target.value as DHCPHAMode)} className="mt-1 w-full border rounded-lg px-3 py-2 dark:bg-gray-800 dark:border-gray-600 dark:text-white">
              <option value={DHCPHAMode.HOT_STANDBY}>Hot standby</option>
              <option value={DHCPHAMode.LOAD_BALANCING}>Load balancing</option>
            </select>
          </label>
          <label className="block">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">HA Peer Address</span>
            <input value={haPeerAddress} onChange={(event) => setHaPeerAddress(event.target.value)} className="mt-1 w-full border rounded-lg px-3 py-2 dark:bg-gray-800 dark:border-gray-600 dark:text-white" placeholder="10.0.0.2" />
          </label>
        </>
      ) : null}
      <div className="flex justify-end">
        <button disabled={loading} className="px-4 py-2 rounded-lg bg-primary-600 text-white disabled:opacity-50">
          {loading ? 'Creating...' : 'Create Server'}
        </button>
      </div>
    </form>
  )
}

function DHCPSubnetForm({
  loading,
  onSubmit,
}: {
  loading: boolean
  onSubmit: (payload: DHCPSubnetCreate) => Promise<void>
}) {
  const [name, setName] = useState('lan-subnet')
  const [subnet, setSubnet] = useState('192.168.10.0/24')
  const [type, setType] = useState(DHCPSubnetType.V4)
  const [routers, setRouters] = useState('192.168.10.1')
  const [dnsServers, setDnsServers] = useState('192.168.10.53')
  const [leaseMin, setLeaseMin] = useState(300)
  const [leaseDefault, setLeaseDefault] = useState(3600)
  const [leaseMax, setLeaseMax] = useState(7200)
  const [delegatedPrefixLength, setDelegatedPrefixLength] = useState('')

  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault()
        void onSubmit({
          name,
          subnet,
          type,
          routers: routers.split(',').map((item) => item.trim()).filter(Boolean),
          dns_servers: dnsServers.split(',').map((item) => item.trim()).filter(Boolean),
          lease_time_min: leaseMin,
          lease_time_default: leaseDefault,
          lease_time_max: leaseMax,
          delegated_prefix_length: delegatedPrefixLength ? Number(delegatedPrefixLength) : undefined,
        })
      }}
    >
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <label className="block">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Name</span>
          <input value={name} onChange={(event) => setName(event.target.value)} className="mt-1 w-full border rounded-lg px-3 py-2 dark:bg-gray-800 dark:border-gray-600 dark:text-white" />
        </label>
        <label className="block">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Type</span>
          <select value={type} onChange={(event) => setType(event.target.value as DHCPSubnetType)} className="mt-1 w-full border rounded-lg px-3 py-2 dark:bg-gray-800 dark:border-gray-600 dark:text-white">
            <option value={DHCPSubnetType.V4}>IPv4</option>
            <option value={DHCPSubnetType.V6}>IPv6</option>
          </select>
        </label>
      </div>
      <label className="block">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Subnet CIDR</span>
        <input value={subnet} onChange={(event) => setSubnet(event.target.value)} className="mt-1 w-full border rounded-lg px-3 py-2 dark:bg-gray-800 dark:border-gray-600 dark:text-white" />
      </label>
      <label className="block">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Routers (comma separated)</span>
        <input value={routers} onChange={(event) => setRouters(event.target.value)} className="mt-1 w-full border rounded-lg px-3 py-2 dark:bg-gray-800 dark:border-gray-600 dark:text-white" />
      </label>
      <label className="block">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">DNS servers (comma separated)</span>
        <input value={dnsServers} onChange={(event) => setDnsServers(event.target.value)} className="mt-1 w-full border rounded-lg px-3 py-2 dark:bg-gray-800 dark:border-gray-600 dark:text-white" />
      </label>
      <div className="grid grid-cols-3 gap-3">
        <label className="block">
          <span className="text-xs font-medium text-gray-700 dark:text-gray-300">Min</span>
          <input type="number" value={leaseMin} onChange={(event) => setLeaseMin(Number(event.target.value))} className="mt-1 w-full border rounded-lg px-3 py-2 dark:bg-gray-800 dark:border-gray-600 dark:text-white" />
        </label>
        <label className="block">
          <span className="text-xs font-medium text-gray-700 dark:text-gray-300">Default</span>
          <input type="number" value={leaseDefault} onChange={(event) => setLeaseDefault(Number(event.target.value))} className="mt-1 w-full border rounded-lg px-3 py-2 dark:bg-gray-800 dark:border-gray-600 dark:text-white" />
        </label>
        <label className="block">
          <span className="text-xs font-medium text-gray-700 dark:text-gray-300">Max</span>
          <input type="number" value={leaseMax} onChange={(event) => setLeaseMax(Number(event.target.value))} className="mt-1 w-full border rounded-lg px-3 py-2 dark:bg-gray-800 dark:border-gray-600 dark:text-white" />
        </label>
      </div>
      {type === DHCPSubnetType.V6 ? (
        <label className="block">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Delegated Prefix Length (optional)</span>
          <input value={delegatedPrefixLength} onChange={(event) => setDelegatedPrefixLength(event.target.value)} className="mt-1 w-full border rounded-lg px-3 py-2 dark:bg-gray-800 dark:border-gray-600 dark:text-white" placeholder="64" />
        </label>
      ) : null}
      <div className="flex justify-end">
        <button disabled={loading} className="px-4 py-2 rounded-lg bg-primary-600 text-white disabled:opacity-50">
          {loading ? 'Creating...' : 'Create Subnet'}
        </button>
      </div>
    </form>
  )
}

function DHCPPoolForm({
  subnetType,
  loading,
  onSubmit,
}: {
  subnetType: DHCPSubnetType
  loading: boolean
  onSubmit: (payload: DHCPPoolCreate) => Promise<void>
}) {
  const [startAddress, setStartAddress] = useState(subnetType === DHCPSubnetType.V4 ? '192.168.10.100' : '2001:db8::100')
  const [endAddress, setEndAddress] = useState(subnetType === DHCPSubnetType.V4 ? '192.168.10.200' : '2001:db8::1ff')

  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault()
        void onSubmit({ start_address: startAddress, end_address: endAddress, type: subnetType })
      }}
    >
      <label className="block">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Start Address</span>
        <input value={startAddress} onChange={(event) => setStartAddress(event.target.value)} className="mt-1 w-full border rounded-lg px-3 py-2 dark:bg-gray-800 dark:border-gray-600 dark:text-white" />
      </label>
      <label className="block">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">End Address</span>
        <input value={endAddress} onChange={(event) => setEndAddress(event.target.value)} className="mt-1 w-full border rounded-lg px-3 py-2 dark:bg-gray-800 dark:border-gray-600 dark:text-white" />
      </label>
      <div className="flex justify-end">
        <button disabled={loading} className="px-4 py-2 rounded-lg bg-primary-600 text-white disabled:opacity-50">
          {loading ? 'Creating...' : 'Create Pool'}
        </button>
      </div>
    </form>
  )
}

function DHCPReservationForm({
  subnetType,
  loading,
  onSubmit,
}: {
  subnetType: DHCPSubnetType
  loading: boolean
  onSubmit: (payload: DHCPReservationCreate) => Promise<void>
}) {
  const [hostname, setHostname] = useState('host-01')
  const [ipAddress, setIpAddress] = useState(subnetType === DHCPSubnetType.V4 ? '192.168.10.10' : '2001:db8::10')
  const [hwAddress, setHwAddress] = useState(subnetType === DHCPSubnetType.V4 ? '52:54:00:12:34:56' : '00:03:00:01:52:54:00:12:34:56')

  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault()
        void onSubmit({
          hostname,
          ip_address: ipAddress,
          hw_address: hwAddress,
          type: subnetType,
        })
      }}
    >
      <label className="block">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Hostname</span>
        <input value={hostname} onChange={(event) => setHostname(event.target.value)} className="mt-1 w-full border rounded-lg px-3 py-2 dark:bg-gray-800 dark:border-gray-600 dark:text-white" />
      </label>
      <label className="block">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">IP Address</span>
        <input value={ipAddress} onChange={(event) => setIpAddress(event.target.value)} className="mt-1 w-full border rounded-lg px-3 py-2 dark:bg-gray-800 dark:border-gray-600 dark:text-white" />
      </label>
      <label className="block">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{subnetType === DHCPSubnetType.V4 ? 'MAC Address' : 'DUID'}</span>
        <input value={hwAddress} onChange={(event) => setHwAddress(event.target.value)} className="mt-1 w-full border rounded-lg px-3 py-2 dark:bg-gray-800 dark:border-gray-600 dark:text-white" />
      </label>
      <div className="flex justify-end">
        <button disabled={loading} className="px-4 py-2 rounded-lg bg-primary-600 text-white disabled:opacity-50">
          {loading ? 'Creating...' : 'Create Reservation'}
        </button>
      </div>
    </form>
  )
}

function DHCPOptionForm({
  subnetType,
  loading,
  onSubmit,
}: {
  subnetType: DHCPSubnetType
  loading: boolean
  onSubmit: (payload: DHCPOptionCreate) => Promise<void>
}) {
  const [optionCode, setOptionCode] = useState(subnetType === DHCPSubnetType.V4 ? 66 : 23)
  const [optionName, setOptionName] = useState(subnetType === DHCPSubnetType.V4 ? 'tftp-server-name' : 'dns-servers')
  const [optionValue, setOptionValue] = useState(subnetType === DHCPSubnetType.V4 ? '192.168.10.2' : '2001:db8::53')

  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault()
        void onSubmit({
          option_code: optionCode,
          option_name: optionName,
          option_value: optionValue,
          type: subnetType,
        })
      }}
    >
      <label className="block">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Option Code</span>
        <input type="number" value={optionCode} onChange={(event) => setOptionCode(Number(event.target.value))} className="mt-1 w-full border rounded-lg px-3 py-2 dark:bg-gray-800 dark:border-gray-600 dark:text-white" />
      </label>
      <label className="block">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Option Name</span>
        <input value={optionName} onChange={(event) => setOptionName(event.target.value)} className="mt-1 w-full border rounded-lg px-3 py-2 dark:bg-gray-800 dark:border-gray-600 dark:text-white" />
      </label>
      <label className="block">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Option Value</span>
        <input value={optionValue} onChange={(event) => setOptionValue(event.target.value)} className="mt-1 w-full border rounded-lg px-3 py-2 dark:bg-gray-800 dark:border-gray-600 dark:text-white" />
      </label>
      <div className="flex justify-end">
        <button disabled={loading} className="px-4 py-2 rounded-lg bg-primary-600 text-white disabled:opacity-50">
          {loading ? 'Creating...' : 'Create Option'}
        </button>
      </div>
    </form>
  )
}
