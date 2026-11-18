import { useEffect, useMemo, useState } from 'react'
import {
  Info,
  Plus,
  Trash2,
  Play,
  Square,
  RotateCw,
  Search,
  Pencil,
} from 'lucide-react'

import { useInstanceStore } from '../../stores/instance'
import { useAuthStore } from '../../stores/auth'
import {
  useBulkDeleteDNSRecords,
  useBulkUpdateDNSRecords,
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
  useUpdateDNSRecord,
} from '../../hooks/useApi'
import {
  Badge,
  Button,
  Card,
  Checkbox,
  ConfirmDialog,
  Field,
  IconButton,
  Input,
  Modal,
  PageHeader,
  QueryError,
  Select,
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
  DNSRecordCreate,
  DNSZone,
  DNSServer,
} from '../../types'
import { DNSRecordType, DNSZoneType } from '../../types'

export function DNSServers() {
  const { selectedInstanceId } = useInstanceStore()
  const { user } = useAuthStore()
  const isAdmin = user?.role === 'admin' || user?.role === 'superadmin'

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
  const [recordSearch, setRecordSearch] = useState('')
  const [recordTypeFilter, setRecordTypeFilter] = useState<string>('')

  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
  const [editTarget, setEditTarget] = useState<DNSRecord | null>(null)
  const [bulkEditOpen, setBulkEditOpen] = useState(false)
  const [bulkDeleteOpen, setBulkDeleteOpen] = useState(false)
  const [bulkTtl, setBulkTtl] = useState('3600')

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
  const createRecordMutation = useCreateDNSRecord(selectedZone?.id || 0, selectedServer?.id)

  const deleteServerMutation = useDeleteDNSServer(selectedInstanceId || 0)
  const deleteZoneMutation = useDeleteDNSZone(selectedServer?.id || 0)
  const deleteRecordMutation = useDeleteDNSRecord(selectedZone?.id || 0, selectedServer?.id)

  const updateRecordMutation = useUpdateDNSRecord(selectedZone?.id || 0, selectedServer?.id)
  const bulkUpdateMutation = useBulkUpdateDNSRecords(selectedZone?.id || 0, selectedServer?.id)
  const bulkDeleteMutation = useBulkDeleteDNSRecords(selectedZone?.id || 0, selectedServer?.id)

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

  const filteredRecords = useMemo(() => {
    if (!records) return []
    const q = recordSearch.trim().toLowerCase()
    return records.filter((record) => {
      if (recordTypeFilter && record.record_type !== recordTypeFilter) return false
      if (!q) return true
      return (
        record.name.toLowerCase().includes(q) ||
        record.content.toLowerCase().includes(q)
      )
    })
  }, [records, recordSearch, recordTypeFilter])

  /* ── Selection state (admin-only bulk layer) ─────────────────────── */

  // Switching zone (or server) also resets the filters, for a clean slate.
  useEffect(() => {
    setSelectedIds(new Set())
    setRecordSearch('')
    setRecordTypeFilter('')
    setBulkTtl('3600')
  }, [selectedZone?.id])

  const selectableIds = useMemo(
    () => filteredRecords.filter((record) => !record.is_system).map((record) => record.id),
    [filteredRecords],
  )
  const allSelected =
    selectableIds.length > 0 && selectableIds.every((id) => selectedIds.has(id))

  const toggleRow = (id: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleAll = () => {
    setSelectedIds((prev) => {
      if (selectableIds.length > 0 && selectableIds.every((id) => prev.has(id))) {
        return new Set()
      }
      return new Set(selectableIds)
    })
  }

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

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* ── Servers pane ─────────────────────────────────────────────── */}
        <Card title="Servers" padding="p-0" className="lg:col-span-2">
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
            <div className="divide-y divide-border max-h-[360px] overflow-y-auto">
              {servers.map((server) => (
                <div
                  key={server.id}
                  className={`flex items-center gap-1 ${
                    selectedServer?.id === server.id
                      ? 'bg-primary/5 border-l-2 border-l-primary'
                      : ''
                  }`}
                >
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedServer(server)
                      setSelectedZone(null)
                    }}
                    className="flex-1 min-w-0 text-left px-5 py-3 hover:bg-surface-elevated transition-colors"
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
                  </button>
                  <div className="flex items-center gap-1 pr-4">
                    <IconButton
                      icon={Play}
                      size="sm"
                      variant="ghost"
                      label="Start server"
                      onClick={() => {
                        setActionTarget({ server, action: 'start' })
                      }}
                    />
                    <IconButton
                      icon={Square}
                      size="sm"
                      variant="ghost"
                      label="Stop server"
                      onClick={() => {
                        setActionTarget({ server, action: 'stop' })
                      }}
                    />
                    <IconButton
                      icon={RotateCw}
                      size="sm"
                      variant="ghost"
                      label="Reload server"
                      onClick={() => {
                        setActionTarget({ server, action: 'reload' })
                      }}
                    />
                    <IconButton
                      icon={Trash2}
                      size="sm"
                      variant="ghost"
                      className="text-danger hover:text-danger"
                      label="Delete server"
                      onClick={() => {
                        setDeleteServerTarget(server)
                      }}
                    />
                  </div>
                </div>
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
          className="lg:col-span-3"
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
            <div className="divide-y divide-border max-h-[360px] overflow-y-auto">
              {filteredZones.map((zone) => (
                <div
                  key={zone.id}
                  className={`flex items-center gap-1 ${
                    selectedZone?.id === zone.id
                      ? 'bg-primary/5 border-l-2 border-l-primary'
                      : ''
                  }`}
                >
                  <button
                    type="button"
                    onClick={() => setSelectedZone(zone)}
                    className="flex-1 min-w-0 text-left px-5 py-3 hover:bg-surface-elevated transition-colors"
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
                    <div className="mt-1">
                      {zone.dnssec_enabled ? (
                        <Badge variant="success">DNSSEC</Badge>
                      ) : null}
                    </div>
                  </button>
                  <div className="flex items-center gap-2 pr-4">
                    <IconButton
                      icon={Trash2}
                      size="sm"
                      variant="ghost"
                      className="text-danger hover:text-danger"
                      label="Delete zone"
                      onClick={() => {
                        setDeleteZoneTarget(zone)
                      }}
                    />
                  </div>
                </div>
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
      </div>

      {/* ── Zone Entries — full-width, below the selection cards ──────── */}
      <Card
        title={`Zone Entries${selectedZone ? ` — ${selectedZone.name}` : ''}`}
        padding="p-0"
        actions={
          isAdmin ? (
            <Button
              size="sm"
              variant="secondary"
              disabled={!selectedZone}
              onClick={() => setCreateRecordOpen(true)}
            >
              Add
            </Button>
          ) : null
        }
      >
        {!selectedZone ? (
          <div className="p-5 text-sm text-on-surface-muted">
            Select a zone to view its entries.
          </div>
        ) : recordsLoading ? (
          <div className="p-5 space-y-3">
            {Array.from({ length: 4 }, (_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : recordsError ? (
          <div className="p-5">
            <QueryError onRetry={refetchRecords} />
          </div>
        ) : (
          <>
            {/* Toolbar — text + type filters, plus the bulk selection bar */}
            <div className="flex items-center gap-3 px-5 py-3 border-b border-border">
              <Input
                value={recordSearch}
                onChange={(event) => setRecordSearch(event.target.value)}
                placeholder="Filter entries…"
                className="flex-1"
              />
              <div className="w-40 shrink-0">
                <Select
                  value={recordTypeFilter}
                  onChange={(event) => setRecordTypeFilter(event.target.value)}
                  aria-label="Filter by record type"
                >
                  <option value="">All types</option>
                  {recordTypeOptions.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </Select>
              </div>
              {isAdmin && selectedIds.size > 0 && (
                <div className="ml-auto flex items-center gap-2 shrink-0">
                  <span className="text-sm text-on-surface-muted whitespace-nowrap">
                    {selectedIds.size} selected
                  </span>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => setBulkEditOpen(true)}
                  >
                    Edit Selected
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => setBulkDeleteOpen(true)}
                  >
                    Delete Selected
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setSelectedIds(new Set())}
                  >
                    Clear
                  </Button>
                </div>
              )}
            </div>

            {filteredRecords.length > 0 ? (
              <div className="max-h-[830px] overflow-y-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-xs uppercase tracking-wide text-on-surface-muted border-b border-border">
                      {isAdmin ? (
                        <th className="w-10 px-2">
                          <Checkbox
                            aria-label="Select all records"
                            checked={allSelected}
                            onChange={toggleAll}
                          />
                        </th>
                      ) : (
                        <th className="w-10" />
                      )}
                      <th className="px-4 py-2.5 text-left font-medium">Name</th>
                      <th className="px-4 py-2.5 text-left font-medium">Type</th>
                      <th className="px-4 py-2.5 text-left font-medium">TTL</th>
                      <th className="px-4 py-2.5 text-left font-medium">Content</th>
                      <th className="px-4 py-2.5 text-right w-24 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {filteredRecords.map((record) => (
                      <tr
                        key={record.id}
                        className={`hover:bg-surface-elevated transition-colors ${
                          selectedIds.has(record.id) ? 'bg-primary/5' : ''
                        }`}
                      >
                        {isAdmin && !record.is_system ? (
                          <td className="w-10 px-2">
                            <Checkbox
                              aria-label={`Select ${record.name} ${record.record_type}`}
                              checked={selectedIds.has(record.id)}
                              onChange={() => toggleRow(record.id)}
                            />
                          </td>
                        ) : (
                          <td className="w-10" />
                        )}
                        <td className="px-4 py-3 font-mono font-medium text-on-surface">
                          {record.name}
                        </td>
                        <td className="px-4 py-3">
                          <Badge variant="info" className="uppercase">
                            {record.record_type}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 font-mono text-on-surface-muted">
                          {record.ttl}
                        </td>
                        <td
                          className="px-4 py-3 font-mono text-on-surface-muted max-w-[24rem] truncate"
                          title={record.content}
                        >
                          {record.content}
                        </td>
                        <td className="px-4 py-3 text-right">
                          {record.is_system ? (
                            <Badge variant="neutral">system</Badge>
                          ) : isAdmin ? (
                            <div className="inline-flex items-center gap-1">
                              <IconButton
                                icon={Pencil}
                                size="sm"
                                variant="ghost"
                                label="Edit record"
                                onClick={() => setEditTarget(record)}
                              />
                              <IconButton
                                icon={Trash2}
                                size="sm"
                                variant="ghost"
                                className="text-danger hover:text-danger"
                                label="Delete record"
                                onClick={() => setDeleteRecordTarget(record)}
                              />
                            </div>
                          ) : null}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-5 text-sm text-on-surface-muted">
                No records in this zone.
              </div>
            )}
          </>
        )}
      </Card>

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
          zoneName={selectedZone?.name}
          onSubmit={async (payload) => {
            await createRecordMutation.mutateAsync(payload as DNSRecordCreate)
            toast.success('Record created')
            setCreateRecordOpen(false)
          }}
        />
      </Modal>

      {/* ── Edit Record modal ────────────────────────────────────────── */}
      <Modal
        open={!!editTarget}
        onClose={() => setEditTarget(null)}
        title="Edit Record"
      >
        <DNSRecordForm
          initial={editTarget ?? undefined}
          loading={updateRecordMutation.isPending}
          onCancel={() => setEditTarget(null)}
          recordTypeOptions={recordTypeOptions}
          zoneName={selectedZone?.name}
          onSubmit={async (payload) => {
            if (!editTarget) return
            await updateRecordMutation.mutateAsync({ id: editTarget.id, ...payload })
            toast.success('Record updated')
            setEditTarget(null)
          }}
        />
      </Modal>

      {/* ── Bulk Edit modal (TTL only) ───────────────────────────────── */}
      <Modal
        open={bulkEditOpen}
        onClose={() => setBulkEditOpen(false)}
        title={`Bulk Edit — ${selectedIds.size} records`}
        size="sm"
      >
        <div className="space-y-4">
          <Field label="TTL" required>
            <Input
              type="number"
              value={bulkTtl}
              onChange={(event) => setBulkTtl(event.target.value)}
            />
          </Field>
          <p className="text-sm text-on-surface-muted">
            Applied to all {selectedIds.size} selected records. Names, types and
            values stay untouched.
          </p>
          <div className="flex justify-end gap-3">
            <Button
              variant="secondary"
              onClick={() => setBulkEditOpen(false)}
            >
              Cancel
            </Button>
            <Button
              loading={bulkUpdateMutation.isPending}
              onClick={() => {
                const ids = [...selectedIds]
                void bulkUpdateMutation
                  .mutateAsync({ record_ids: ids, changes: { ttl: Number(bulkTtl) } })
                  .then(() => {
                    toast.success(`Updated ${ids.length} records`)
                    setSelectedIds(new Set())
                    setBulkEditOpen(false)
                  })
              }}
            >
              Apply to {selectedIds.size} records
            </Button>
          </div>
        </div>
      </Modal>

      {/* ── Bulk Delete ConfirmDialog ────────────────────────────────── */}
      <ConfirmDialog
        open={bulkDeleteOpen}
        onClose={() => setBulkDeleteOpen(false)}
        variant="danger"
        title={`Delete ${selectedIds.size} Records`}
        message={`Delete ${selectedIds.size} selected records from ${selectedZone?.name}?`}
        impact="This immediately removes the records and pushes the new zone configuration to the DNS agent."
        confirmLabel={`Delete ${selectedIds.size} Records`}
        loading={bulkDeleteMutation.isPending}
        onConfirm={() => {
          const ids = [...selectedIds]
          void bulkDeleteMutation
            .mutateAsync(ids)
            .then(() => {
              toast.success(`Deleted ${ids.length} records`)
              setSelectedIds(new Set())
              setBulkDeleteOpen(false)
            })
        }}
      />

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
