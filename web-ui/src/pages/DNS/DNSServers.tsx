import { useMemo, useState } from 'react'
import {
  Info,
  Plus,
  Trash2,
  Play,
  Square,
  RotateCw,
  Search,
} from 'lucide-react'

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
  Badge,
  Button,
  Card,
  ConfirmDialog,
  IconButton,
  Input,
  Modal,
  PageHeader,
  QueryError,
  Skeleton,
  SkeletonText,
  StatusBadge,
  toast,
} from '../../components/ui'
import { DNSServerForm } from '../../components/forms/DNSServerForm'
import { DNSZoneForm } from '../../components/forms/DNSZoneForm'
import { DNSRecordForm } from '../../components/forms/DNSRecordForm'
import type {
  DNSRecord,
  DNSZone,
  DNSServer,
} from '../../types'
import { DNSRecordType, DNSZoneType } from '../../types'

export function DNSServers() {
  const { selectedInstanceId } = useInstanceStore()

  const [selectedServer, setSelectedServer] = useState<DNSServer | null>(null)
  const [selectedZone, setSelectedZone] = useState<DNSZone | null>(null)

  const [createServerOpen, setCreateServerOpen] = useState(false)
  const [createZoneOpen, setCreateZoneOpen] = useState(false)
  const [createRecordOpen, setCreateRecordOpen] = useState(false)

  const [deleteServerTarget, setDeleteServerTarget] =
    useState<DNSServer | null>(null)
  const [deleteZoneTarget, setDeleteZoneTarget] = useState<DNSZone | null>(null)
  const [deleteRecordTarget, setDeleteRecordTarget] =
    useState<DNSRecord | null>(null)

  const [actionTarget, setActionTarget] = useState<{
    server: DNSServer
    action: 'start' | 'stop' | 'reload'
  } | null>(null)

  const [zoneSearch, setZoneSearch] = useState('')

  const {
    data: servers,
    isLoading: serversLoading,
    isError: serversError,
    refetch: refetchServers,
  } = useDNSServers(selectedInstanceId || 0)
  const {
    data: zones,
    isLoading: zonesLoading,
    isError: zonesError,
    refetch: refetchZones,
  } = useDNSZones(selectedServer?.id || 0)
  const {
    data: records,
    isLoading: recordsLoading,
    isError: recordsError,
    refetch: refetchRecords,
  } = useDNSRecords(selectedZone?.id || 0)

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

  const filteredZones = useMemo(() => {
    if (!zones) return []
    if (!zoneSearch.trim()) return zones
    const q = zoneSearch.toLowerCase()
    return zones.filter((z) => z.name.toLowerCase().includes(q))
  }, [zones, zoneSearch])

  /* ── No instance selected ── */
  if (!selectedInstanceId) {
    return (
      <div>
        <PageHeader title="DNS Servers" />
        <Card className="mt-6">
          <div className="flex items-center gap-3 text-on-surface-muted">
            <Info className="h-5 w-5 shrink-0" />
            <p className="text-sm">Select an instance from the top bar to manage its DNS servers.</p>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="DNS Servers"
        description="Public/private zones, DNSSEC, forwarding, and reverse DNS"
        primaryAction={
          <Button onClick={() => setCreateServerOpen(true)}>
            <Plus className="w-4 h-4" />
            New DNS Server
          </Button>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
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
                    setSelectedZone(null)
                  }}
                  className={`w-full text-left px-5 py-3 hover:bg-surface-elevated transition-colors ${
                    selectedServer?.id === server.id
                      ? 'bg-primary/5 border-l-2 border-l-primary'
                      : ''
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium text-on-surface truncate">
                      {server.name}
                    </span>
                    <StatusBadge status={server.status} />
                  </div>
                  <div className="mt-1 text-xs text-on-surface-muted">
                    {server.zones_count} zones · {server.port}/tcp+udp
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
              No DNS servers yet.
            </div>
          )}
        </Card>

        {/* ── Zones pane ──────────────────────────────────────────────── */}
        <Card
          title="Zones"
          padding="p-0"
          actions={
            <Button
              size="sm"
              variant="secondary"
              disabled={!selectedServer}
              onClick={() => setCreateZoneOpen(true)}
            >
              Add
            </Button>
          }
        >
          {/* Zone search */}
          <div className="px-5 py-3 border-b border-border">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-muted" />
              <Input
                value={zoneSearch}
                onChange={(event) => setZoneSearch(event.target.value)}
                placeholder="Search zones…"
                className="pl-8"
              />
            </div>
          </div>

          {zonesLoading ? (
            <div className="p-5 space-y-3">
              {Array.from({ length: 3 }, (_, i) => (
                <SkeletonText key={i} lines={2} />
              ))}
            </div>
          ) : zonesError ? (
            <div className="p-5">
              <QueryError onRetry={refetchZones} />
            </div>
          ) : filteredZones.length > 0 ? (
            <div className="divide-y divide-border max-h-[420px] overflow-y-auto">
              {filteredZones.map((zone) => (
                <button
                  key={zone.id}
                  type="button"
                  onClick={() => setSelectedZone(zone)}
                  className={`w-full text-left px-5 py-3 hover:bg-surface-elevated transition-colors ${
                    selectedZone?.id === zone.id
                      ? 'bg-primary/5 border-l-2 border-l-primary'
                      : ''
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium text-on-surface truncate">
                      {zone.name}
                    </span>
                    <Badge variant="neutral">{zone.zone_type}</Badge>
                  </div>
                  <div className="mt-1 text-xs text-on-surface-muted">
                    serial {zone.serial} · {zone.records_count} records
                  </div>
                  <div className="mt-2 flex items-center gap-2">
                    {zone.dnssec_enabled ? (
                      <Badge variant="success">DNSSEC</Badge>
                    ) : null}
                    <IconButton
                      icon={Trash2}
                      size="sm"
                      variant="ghost"
                      className="text-danger hover:text-danger"
                      label="Delete zone"
                      onClick={(event) => {
                        event.stopPropagation()
                        setDeleteZoneTarget(zone)
                      }}
                    />
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div className="p-5 text-sm text-on-surface-muted">
              {selectedServer
                ? 'No zones for this server.'
                : 'Select a server to view zones.'}
            </div>
          )}
        </Card>

        {/* ── Records pane ────────────────────────────────────────────── */}
        <Card
          title="Records"
          padding="p-0"
          actions={
            <Button
              size="sm"
              variant="secondary"
              disabled={!selectedZone}
              onClick={() => setCreateRecordOpen(true)}
            >
              Add
            </Button>
          }
        >
          {recordsLoading ? (
            <div className="p-5 space-y-3">
              {Array.from({ length: 4 }, (_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : recordsError ? (
            <div className="p-5">
              <QueryError onRetry={refetchRecords} />
            </div>
          ) : records && records.length > 0 ? (
            <div className="divide-y divide-border max-h-[420px] overflow-y-auto">
              {records.map((record) => (
                <div
                  key={record.id}
                  className="px-5 py-3 flex items-center justify-between gap-3"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm font-medium text-on-surface truncate">
                        {record.name}
                      </span>
                      <Badge variant="info">{record.record_type}</Badge>
                    </div>
                    <div className="text-xs text-on-surface-muted mt-1 flex items-center gap-3">
                      <span className="font-mono">TTL {record.ttl}</span>
                      <span className="font-mono truncate">
                        {record.content}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    {!record.is_system ? (
                      <IconButton
                        icon={Trash2}
                        size="sm"
                        variant="ghost"
                        className="text-danger hover:text-danger"
                        label="Delete record"
                        onClick={() => setDeleteRecordTarget(record)}
                      />
                    ) : (
                      <Badge variant="info">system</Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-5 text-sm text-on-surface-muted">
              {selectedZone
                ? 'No records in this zone.'
                : 'Select a zone to view records.'}
            </div>
          )}
        </Card>
      </div>

      {/* ── Create Server modal ──────────────────────────────────────── */}
      <Modal
        open={createServerOpen}
        onClose={() => setCreateServerOpen(false)}
        title="Create DNS Server"
      >
        <DNSServerForm
          loading={createServerMutation.isPending}
          onSubmit={async (payload) => {
            await createServerMutation.mutateAsync(payload)
            toast.success('DNS server created')
            setCreateServerOpen(false)
          }}
        />
      </Modal>

      {/* ── Create Zone modal ────────────────────────────────────────── */}
      <Modal
        open={createZoneOpen}
        onClose={() => setCreateZoneOpen(false)}
        title="Create Zone"
      >
        <DNSZoneForm
          zoneTypeOptions={zoneTypeOptions}
          loading={createZoneMutation.isPending}
          onSubmit={async (payload) => {
            await createZoneMutation.mutateAsync(payload)
            toast.success('Zone created')
            setCreateZoneOpen(false)
          }}
        />
      </Modal>

      {/* ── Create Record modal ──────────────────────────────────────── */}
      <Modal
        open={createRecordOpen}
        onClose={() => setCreateRecordOpen(false)}
        title="Create Record"
      >
        <DNSRecordForm
          recordTypeOptions={recordTypeOptions}
          loading={createRecordMutation.isPending}
          onSubmit={async (payload) => {
            await createRecordMutation.mutateAsync(payload)
            toast.success('Record created')
            setCreateRecordOpen(false)
          }}
        />
      </Modal>

      {/* ── Server action ConfirmDialog (Start/Stop/Reload) ───────────── */}
      <ConfirmDialog
        open={!!actionTarget}
        onClose={() => setActionTarget(null)}
        variant="warning"
        confirmLabel={actionTarget?.action === 'start' ? 'Start' : actionTarget?.action === 'stop' ? 'Stop' : 'Reload'}
        title={`${actionTarget?.action === 'start' ? 'Start' : actionTarget?.action === 'stop' ? 'Stop' : 'Reload'} DNS Server`}
        message={`${actionTarget?.action === 'start' ? 'Start' : actionTarget?.action === 'stop' ? 'Stop' : 'Reload'} ${actionTarget?.server.name}?`}
        impact={
          actionTarget?.action === 'stop'
            ? 'Stopping the server will interrupt DNS resolution for all clients.'
            : actionTarget?.action === 'reload'
              ? 'Reloading applies pending configuration changes without dropping active queries.'
              : undefined
        }
        loading={actionMutation.isPending}
        onConfirm={() => {
          if (!actionTarget) return
          void actionMutation
            .mutateAsync({
              serverId: actionTarget.server.id,
              action: actionTarget.action,
            })
            .then(() => {
              toast.success(`Server ${actionTarget.action}ed`)
              setActionTarget(null)
            })
        }}
      />

      {/* ── Delete Server ConfirmDialog ───────────────────────────────── */}
      <ConfirmDialog
        open={!!deleteServerTarget}
        onClose={() => setDeleteServerTarget(null)}
        title="Delete DNS Server"
        message={`Delete ${deleteServerTarget?.name}?`}
        impact="This will remove all associated zones and records."
        loading={deleteServerMutation.isPending}
        onConfirm={() => {
          if (!deleteServerTarget) return
          void deleteServerMutation
            .mutateAsync(deleteServerTarget.id)
            .then(() => {
              if (selectedServer?.id === deleteServerTarget.id) {
                setSelectedServer(null)
                setSelectedZone(null)
              }
              toast.success('DNS server deleted')
              setDeleteServerTarget(null)
            })
        }}
      />

      {/* ── Delete Zone ConfirmDialog ────────────────────────────────── */}
      <ConfirmDialog
        open={!!deleteZoneTarget}
        onClose={() => setDeleteZoneTarget(null)}
        title="Delete DNS Zone"
        message={`Delete zone ${deleteZoneTarget?.name}?`}
        loading={deleteZoneMutation.isPending}
        onConfirm={() => {
          if (!deleteZoneTarget) return
          void deleteZoneMutation
            .mutateAsync(deleteZoneTarget.id)
            .then(() => {
              if (selectedZone?.id === deleteZoneTarget.id) {
                setSelectedZone(null)
              }
              toast.success('Zone deleted')
              setDeleteZoneTarget(null)
            })
        }}
      />

      {/* ── Delete Record ConfirmDialog ──────────────────────────────── */}
      <ConfirmDialog
        open={!!deleteRecordTarget}
        onClose={() => setDeleteRecordTarget(null)}
        title="Delete DNS Record"
        message={`Delete record ${deleteRecordTarget?.name} ${deleteRecordTarget?.record_type}?`}
        loading={deleteRecordMutation.isPending}
        onConfirm={() => {
          if (!deleteRecordTarget) return
          void deleteRecordMutation
            .mutateAsync(deleteRecordTarget.id)
            .then(() => {
              toast.success('Record deleted')
              setDeleteRecordTarget(null)
            })
        }}
      />
    </div>
  )
}
