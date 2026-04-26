import { useMemo, useState } from 'react'
import { Database, Plus, Trash2, Play, Square, RotateCw } from 'lucide-react'

import { useInstanceStore } from '../../stores/instance'
import {
  useCreateDNSRecord,
  useCreateDNSServer,
  useCreateDNSZone,
  useDeleteDNSRecord,
  useDeleteDNSServer,
  useDeleteDNSZone,
  useDNSRecords,
  useDNSServerAction,
  useDNSServers,
  useDNSZones,
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
  DNSRecord,
  DNSRecordCreate,
  DNSZone,
  DNSZoneCreate,
  DNSServer,
  DNSServerCreate,
} from '../../types'
import { DNSRecordType, DNSZoneType } from '../../types'

export function DNSServers() {
  const { selectedInstanceId } = useInstanceStore()

  const [selectedServer, setSelectedServer] = useState<DNSServer | null>(null)
  const [selectedZone, setSelectedZone] = useState<DNSZone | null>(null)

  const [createServerOpen, setCreateServerOpen] = useState(false)
  const [createZoneOpen, setCreateZoneOpen] = useState(false)
  const [createRecordOpen, setCreateRecordOpen] = useState(false)

  const [deleteServerTarget, setDeleteServerTarget] = useState<DNSServer | null>(null)
  const [deleteZoneTarget, setDeleteZoneTarget] = useState<DNSZone | null>(null)
  const [deleteRecordTarget, setDeleteRecordTarget] = useState<DNSRecord | null>(null)

  const { data: servers, isLoading: serversLoading } = useDNSServers(selectedInstanceId || 0)
  const { data: zones, isLoading: zonesLoading } = useDNSZones(selectedServer?.id || 0)
  const { data: records, isLoading: recordsLoading } = useDNSRecords(selectedZone?.id || 0)

  const createServerMutation = useCreateDNSServer(selectedInstanceId || 0)
  const createZoneMutation = useCreateDNSZone(selectedServer?.id || 0)
  const createRecordMutation = useCreateDNSRecord(selectedZone?.id || 0)

  const deleteServerMutation = useDeleteDNSServer(selectedInstanceId || 0)
  const deleteZoneMutation = useDeleteDNSZone(selectedServer?.id || 0)
  const deleteRecordMutation = useDeleteDNSRecord(selectedZone?.id || 0)

  const actionMutation = useDNSServerAction(selectedInstanceId || 0)

  const zoneTypeOptions: DNSZoneType[] = [
    DNSZoneType.MASTER,
    DNSZoneType.SLAVE,
    DNSZoneType.FORWARD,
    DNSZoneType.STUB,
  ]
  const recordTypeOptions: DNSRecordType[] = [
    DNSRecordType.A,
    DNSRecordType.AAAA,
    DNSRecordType.CNAME,
    DNSRecordType.MX,
    DNSRecordType.NS,
    DNSRecordType.PTR,
    DNSRecordType.TXT,
    DNSRecordType.SRV,
    DNSRecordType.CAA,
  ]

  const selectedServerFromList = useMemo(() => {
    if (!servers || !selectedServer) return null
    return servers.find((server) => server.id === selectedServer.id) || null
  }, [servers, selectedServer])

  if (!selectedInstanceId) {
    return (
      <div>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">DNS Servers</h2>
            <p className="text-gray-600 mt-1">Manage authoritative and recursive BIND9 DNS servers</p>
          </div>
        </div>
        <EmptyState icon={Database} title="Select an Instance" description="Choose an instance to manage DNS." />
        <div className="mt-4"><InstanceSelector /></div>
      </div>
    )
  }

  if (serversLoading) return <LoadingSpinner />

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">DNS Servers</h2>
            <p className="text-gray-600 mt-1">Public/private zones, DNSSEC, forwarding, and reverse DNS</p>
          </div>
          <InstanceSelector />
        </div>
        <button
          onClick={() => setCreateServerOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          <Plus className="w-5 h-5" />
          New DNS Server
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-4 py-3 border-b border-gray-200 font-semibold">Servers</div>
          <div className="divide-y divide-gray-100">
            {servers && servers.length > 0 ? servers.map((server) => (
              <button
                key={server.id}
                onClick={() => {
                  setSelectedServer(server)
                  setSelectedZone(null)
                }}
                className={`w-full text-left px-4 py-3 hover:bg-gray-50 ${selectedServer?.id === server.id ? 'bg-primary-50' : ''}`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium text-gray-900 truncate">{server.name}</span>
                  <StatusBadge status={server.status} />
                </div>
                <div className="mt-1 text-xs text-gray-500">
                  {server.zones_count} zones · {server.port}/tcp+udp
                </div>
                <div className="mt-2 flex items-center gap-2">
                  <button
                    onClick={(event) => {
                      event.stopPropagation()
                      void actionMutation.mutateAsync({ serverId: server.id, action: 'start' })
                    }}
                    className="p-1 rounded text-green-700 hover:bg-green-100"
                    title="Start"
                  >
                    <Play className="w-4 h-4" />
                  </button>
                  <button
                    onClick={(event) => {
                      event.stopPropagation()
                      void actionMutation.mutateAsync({ serverId: server.id, action: 'stop' })
                    }}
                    className="p-1 rounded text-gray-700 hover:bg-gray-100"
                    title="Stop"
                  >
                    <Square className="w-4 h-4" />
                  </button>
                  <button
                    onClick={(event) => {
                      event.stopPropagation()
                      void actionMutation.mutateAsync({ serverId: server.id, action: 'reload' })
                    }}
                    className="p-1 rounded text-blue-700 hover:bg-blue-100"
                    title="Reload"
                  >
                    <RotateCw className="w-4 h-4" />
                  </button>
                  <button
                    onClick={(event) => {
                      event.stopPropagation()
                      setDeleteServerTarget(server)
                    }}
                    className="p-1 rounded text-red-700 hover:bg-red-100"
                    title="Delete"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </button>
            )) : (
              <div className="p-4 text-sm text-gray-500">No DNS servers yet.</div>
            )}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-4 py-3 border-b border-gray-200 font-semibold flex items-center justify-between">
            <span>Zones</span>
            <button
              disabled={!selectedServer}
              onClick={() => setCreateZoneOpen(true)}
              className="text-sm px-2 py-1 rounded bg-primary-600 text-white disabled:opacity-40"
            >
              Add
            </button>
          </div>
          {zonesLoading ? <div className="p-4"><LoadingSpinner /></div> : (
            <div className="divide-y divide-gray-100">
              {zones && zones.length > 0 ? zones.map((zone) => (
                <button
                  key={zone.id}
                  onClick={() => setSelectedZone(zone)}
                  className={`w-full text-left px-4 py-3 hover:bg-gray-50 ${selectedZone?.id === zone.id ? 'bg-primary-50' : ''}`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium text-gray-900 truncate">{zone.name}</span>
                    <span className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-700 uppercase">{zone.zone_type}</span>
                  </div>
                  <div className="mt-1 text-xs text-gray-500">
                    serial {zone.serial} · {zone.records_count} records
                  </div>
                  <div className="mt-2 flex items-center gap-2">
                    {zone.dnssec_enabled ? <span className="text-xs px-2 py-0.5 rounded bg-green-100 text-green-700">DNSSEC</span> : null}
                    <button
                      onClick={(event) => {
                        event.stopPropagation()
                        setDeleteZoneTarget(zone)
                      }}
                      className="p-1 rounded text-red-700 hover:bg-red-100"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </button>
              )) : (
                <div className="p-4 text-sm text-gray-500">No zones for this server.</div>
              )}
            </div>
          )}
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-4 py-3 border-b border-gray-200 font-semibold flex items-center justify-between">
            <span>Records</span>
            <button
              disabled={!selectedZone}
              onClick={() => setCreateRecordOpen(true)}
              className="text-sm px-2 py-1 rounded bg-primary-600 text-white disabled:opacity-40"
            >
              Add
            </button>
          </div>
          {recordsLoading ? <div className="p-4"><LoadingSpinner /></div> : (
            <div className="divide-y divide-gray-100 max-h-[420px] overflow-y-auto">
              {records && records.length > 0 ? records.map((record) => (
                <div key={record.id} className="px-4 py-3">
                  <div className="flex items-center justify-between gap-2">
                    <div className="text-sm font-medium text-gray-900 truncate">{record.name}</div>
                    <span className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-700">{record.record_type}</span>
                  </div>
                  <div className="text-xs text-gray-600 mt-1 break-all">{record.content}</div>
                  <div className="text-xs text-gray-500 mt-1 flex items-center justify-between">
                    <span>TTL {record.ttl}</span>
                    {!record.is_system ? (
                      <button
                        onClick={() => setDeleteRecordTarget(record)}
                        className="p-1 rounded text-red-700 hover:bg-red-100"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    ) : (
                      <span className="text-[11px] px-2 py-0.5 rounded bg-blue-100 text-blue-700">system</span>
                    )}
                  </div>
                </div>
              )) : (
                <div className="p-4 text-sm text-gray-500">No records in this zone.</div>
              )}
            </div>
          )}
        </div>
      </div>

      <Modal open={createServerOpen} onClose={() => setCreateServerOpen(false)} title="Create DNS Server">
        <ServerForm
          loading={createServerMutation.isPending}
          onSubmit={async (payload) => {
            await createServerMutation.mutateAsync(payload)
            setCreateServerOpen(false)
          }}
        />
      </Modal>

      <Modal open={createZoneOpen} onClose={() => setCreateZoneOpen(false)} title="Create Zone">
        <ZoneForm
          zoneTypeOptions={zoneTypeOptions}
          loading={createZoneMutation.isPending}
          onSubmit={async (payload) => {
            await createZoneMutation.mutateAsync(payload)
            setCreateZoneOpen(false)
          }}
        />
      </Modal>

      <Modal open={createRecordOpen} onClose={() => setCreateRecordOpen(false)} title="Create Record">
        <RecordForm
          recordTypeOptions={recordTypeOptions}
          loading={createRecordMutation.isPending}
          onSubmit={async (payload) => {
            await createRecordMutation.mutateAsync(payload)
            setCreateRecordOpen(false)
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
              setSelectedZone(null)
            }
            setDeleteServerTarget(null)
          })
        }}
        title="Delete DNS Server"
        message={`Delete ${deleteServerTarget?.name}? This will remove all associated zones and records.`}
        loading={deleteServerMutation.isPending}
      />

      <ConfirmDialog
        open={!!deleteZoneTarget}
        onClose={() => setDeleteZoneTarget(null)}
        onConfirm={() => {
          if (!deleteZoneTarget) return
          void deleteZoneMutation.mutateAsync(deleteZoneTarget.id).then(() => {
            if (selectedZone?.id === deleteZoneTarget.id) {
              setSelectedZone(null)
            }
            setDeleteZoneTarget(null)
          })
        }}
        title="Delete DNS Zone"
        message={`Delete zone ${deleteZoneTarget?.name}?`}
        loading={deleteZoneMutation.isPending}
      />

      <ConfirmDialog
        open={!!deleteRecordTarget}
        onClose={() => setDeleteRecordTarget(null)}
        onConfirm={() => {
          if (!deleteRecordTarget) return
          void deleteRecordMutation.mutateAsync(deleteRecordTarget.id).then(() => {
            setDeleteRecordTarget(null)
          })
        }}
        title="Delete DNS Record"
        message={`Delete record ${deleteRecordTarget?.name} ${deleteRecordTarget?.record_type}?`}
        loading={deleteRecordMutation.isPending}
      />
    </div>
  )
}

function ServerForm({
  loading,
  onSubmit,
}: {
  loading: boolean
  onSubmit: (payload: DNSServerCreate) => Promise<void>
}) {
  const [name, setName] = useState('dns-server-1')
  const [isRecursive, setIsRecursive] = useState(true)
  const [isAuthoritative, setIsAuthoritative] = useState(true)
  const [forwarders, setForwarders] = useState('1.1.1.1,8.8.8.8')

  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault()
        void onSubmit({
          name,
          is_recursive: isRecursive,
          is_authoritative: isAuthoritative,
          forwarders: forwarders
            .split(',')
            .map((item) => item.trim())
            .filter(Boolean),
        })
      }}
    >
      <label className="block">
        <span className="text-sm font-medium text-gray-700">Name</span>
        <input value={name} onChange={(event) => setName(event.target.value)} className="mt-1 w-full border rounded-lg px-3 py-2" />
      </label>
      <label className="block">
        <span className="text-sm font-medium text-gray-700">Forwarders (comma separated)</span>
        <input value={forwarders} onChange={(event) => setForwarders(event.target.value)} className="mt-1 w-full border rounded-lg px-3 py-2" />
      </label>
      <div className="flex items-center gap-6 text-sm">
        <label className="inline-flex items-center gap-2">
          <input type="checkbox" checked={isRecursive} onChange={(event) => setIsRecursive(event.target.checked)} />
          Recursive
        </label>
        <label className="inline-flex items-center gap-2">
          <input type="checkbox" checked={isAuthoritative} onChange={(event) => setIsAuthoritative(event.target.checked)} />
          Authoritative
        </label>
      </div>
      <div className="flex justify-end">
        <button disabled={loading} className="px-4 py-2 rounded-lg bg-primary-600 text-white disabled:opacity-50">
          {loading ? 'Creating...' : 'Create Server'}
        </button>
      </div>
    </form>
  )
}

function ZoneForm({
  zoneTypeOptions,
  loading,
  onSubmit,
}: {
  zoneTypeOptions: DNSZoneType[]
  loading: boolean
  onSubmit: (payload: DNSZoneCreate) => Promise<void>
}) {
  const [name, setName] = useState('example.internal')
  const [zoneType, setZoneType] = useState<DNSZoneType>(DNSZoneType.MASTER)
  const [dnssecEnabled, setDnssecEnabled] = useState(false)

  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault()
        void onSubmit({
          name,
          zone_type: zoneType,
          dnssec_enabled: dnssecEnabled,
        })
      }}
    >
      <label className="block">
        <span className="text-sm font-medium text-gray-700">Zone Name</span>
        <input value={name} onChange={(event) => setName(event.target.value)} className="mt-1 w-full border rounded-lg px-3 py-2" />
      </label>
      <label className="block">
        <span className="text-sm font-medium text-gray-700">Zone Type</span>
        <select value={zoneType} onChange={(event) => setZoneType(event.target.value as DNSZoneType)} className="mt-1 w-full border rounded-lg px-3 py-2">
          {zoneTypeOptions.map((option) => <option key={option} value={option}>{option}</option>)}
        </select>
      </label>
      <label className="inline-flex items-center gap-2 text-sm">
        <input type="checkbox" checked={dnssecEnabled} onChange={(event) => setDnssecEnabled(event.target.checked)} />
        Enable DNSSEC
      </label>
      <div className="flex justify-end">
        <button disabled={loading} className="px-4 py-2 rounded-lg bg-primary-600 text-white disabled:opacity-50">
          {loading ? 'Creating...' : 'Create Zone'}
        </button>
      </div>
    </form>
  )
}

function RecordForm({
  recordTypeOptions,
  loading,
  onSubmit,
}: {
  recordTypeOptions: DNSRecordType[]
  loading: boolean
  onSubmit: (payload: DNSRecordCreate) => Promise<void>
}) {
  const [name, setName] = useState('@')
  const [recordType, setRecordType] = useState<DNSRecordType>(DNSRecordType.A)
  const [content, setContent] = useState('192.168.1.10')
  const [ttl, setTtl] = useState(3600)

  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault()
        void onSubmit({
          name,
          record_type: recordType,
          content,
          ttl,
        })
      }}
    >
      <label className="block">
        <span className="text-sm font-medium text-gray-700">Name</span>
        <input value={name} onChange={(event) => setName(event.target.value)} className="mt-1 w-full border rounded-lg px-3 py-2" />
      </label>
      <label className="block">
        <span className="text-sm font-medium text-gray-700">Type</span>
        <select value={recordType} onChange={(event) => setRecordType(event.target.value as DNSRecordType)} className="mt-1 w-full border rounded-lg px-3 py-2">
          {recordTypeOptions.map((option) => <option key={option} value={option}>{option}</option>)}
        </select>
      </label>
      <label className="block">
        <span className="text-sm font-medium text-gray-700">Content</span>
        <input value={content} onChange={(event) => setContent(event.target.value)} className="mt-1 w-full border rounded-lg px-3 py-2" />
      </label>
      <label className="block">
        <span className="text-sm font-medium text-gray-700">TTL</span>
        <input type="number" min={0} value={ttl} onChange={(event) => setTtl(Number(event.target.value))} className="mt-1 w-full border rounded-lg px-3 py-2" />
      </label>
      <div className="flex justify-end">
        <button disabled={loading} className="px-4 py-2 rounded-lg bg-primary-600 text-white disabled:opacity-50">
          {loading ? 'Creating...' : 'Create Record'}
        </button>
      </div>
    </form>
  )
}
