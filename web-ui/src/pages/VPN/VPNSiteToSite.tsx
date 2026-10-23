import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowLeft,
  Copy,
  Info,
  KeyRound,
  Network,
  Play,
  Save,
  Square,
} from 'lucide-react'
import { useInstanceStore } from '../../stores/instance'
import {
  useSiteToSiteStatus,
  useInitializeSiteToSite,
  useUpdateVPNServer,
  useVPNServerAction,
  useVPNClients,
  useRegenerateVPNClient,
} from '../../hooks/useApi'
import {
  Badge,
  Button,
  Card,
  CardBody,
  ConfirmDialog,
  EmptyState,
  Field,
  IconButton,
  Input,
  Modal,
  PageHeader,
  QueryError,
  Skeleton,
  SkeletonText,
  toast,
} from '../../components/ui'
import type {
  VPNServerUpdate,
  VPNSiteToSiteStatus,
  VPNRegenerateResponse,
} from '../../types'
import { formatBytes } from '../../utils/format'
import { getErrMsg } from '../../lib/utils'

const WG_KEY_RE = /^[A-Za-z0-9+/]{43}=$/
const ENDPOINT_RE = /^([A-Za-z0-9.-]+|\[[0-9a-fA-F:.]+\])(:\d+)?$/

function handshakeAge(sec: number | null | undefined): string {
  if (sec == null) return 'Never'
  if (sec < 60) return `${sec}s ago`
  const mins = Math.floor(sec / 60)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  return `${hrs}h ago`
}

function TunnelBadge({ row }: { row: VPNSiteToSiteStatus }) {
  if (row.agent === 'offline') {
    return <Badge variant="neutral">Agent offline</Badge>
  }
  if (row.live == null) return <Badge variant="neutral">Unknown</Badge>
  if (row.live.up) return <Badge variant="success">Up</Badge>
  return <Badge variant="danger">Down</Badge>
}

interface InitFormProps {
  endpoint: string
  peerKey: string
  allowedIps: string
  localAddress: string
  keepalive: string
  endpointError: string
  keyError: string
  keepaliveError: string
  loading: boolean
  onChange: (field: string, value: string) => void
  onSubmit: () => void
}

function InitializeForm(props: InitFormProps) {
  return (
    <Card>
      <CardBody>
        <h3 className="text-base font-semibold text-on-surface mb-1">
          Initialize site-to-site tunnel
        </h3>
        <p className="text-sm text-on-surface-muted mb-4">
          Creates a WireGuard site-to-site client tunnel to a remote network and pushes it to
          the VPN agent.
        </p>
        <div className="max-w-lg space-y-4">
          <Field label="Remote endpoint" error={props.endpointError} required>
            <Input
              mono
              value={props.endpoint}
              onChange={(e) => props.onChange('endpoint', e.target.value)}
              placeholder="base0.example.com:51820"
            />
          </Field>
          <Field
            label="Peer public key"
            error={props.keyError}
            required
            helper="The remote network's WireGuard public key (44-char base64)."
          >
            <Input
              mono
              value={props.peerKey}
              onChange={(e) => props.onChange('peerKey', e.target.value)}
              placeholder="kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk="
            />
          </Field>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Field label="Allowed IPs" helper="Default: 10.80.0.0/16">
              <Input
                mono
                value={props.allowedIps}
                onChange={(e) => props.onChange('allowedIps', e.target.value)}
                placeholder="10.80.0.0/16"
              />
            </Field>
            <Field label="Local address" helper="Default: 10.200.0.2/24">
              <Input
                mono
                value={props.localAddress}
                onChange={(e) => props.onChange('localAddress', e.target.value)}
                placeholder="10.200.0.2/24"
              />
            </Field>
            <Field label="Persistent keepalive" error={props.keepaliveError} helper="Seconds, default: 25">
              <Input
                mono
                type="number"
                value={props.keepalive}
                onChange={(e) => props.onChange('keepalive', e.target.value)}
                placeholder="25"
              />
            </Field>
          </div>
          <div className="flex justify-end">
            <Button icon={Network} onClick={props.onSubmit} loading={props.loading}>
              Initialize tunnel
            </Button>
          </div>
        </div>
      </CardBody>
    </Card>
  )
}

interface EditFormProps {
  row: VPNSiteToSiteStatus
  loading: boolean
  onSave: (body: VPNServerUpdate) => void
}

function EditForm({ row, loading, onSave }: EditFormProps) {
  const [endpoint, setEndpoint] = useState(row.remote_endpoint ?? '')
  const [allowedIps, setAllowedIps] = useState(row.allowed_ips ?? '')
  const [keepalive, setKeepalive] = useState(
    row.persistent_keepalive != null ? String(row.persistent_keepalive) : '25',
  )
  const [keepaliveError, setKeepaliveError] = useState('')

  const handleSave = () => {
    const parsed = keepalive.trim()
    let keepaliveValue: number | null = null
    if (parsed !== '') {
      const n = Number(parsed)
      if (!Number.isInteger(n) || n < 0 || n > 65535) {
        setKeepaliveError('Keepalive must be a whole number between 0 and 65535')
        return
      }
      keepaliveValue = n
    }
    setKeepaliveError('')
    onSave({
      endpoint: endpoint.trim() || null,
      allowed_ips: allowedIps.trim() || null,
      persistent_keepalive: keepaliveValue,
    })
  }

  return (
    <Card>
      <CardBody>
        <h3 className="text-base font-semibold text-on-surface mb-4">Tunnel configuration</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Field label="Remote endpoint">
            <Input
              mono
              value={endpoint}
              onChange={(e) => setEndpoint(e.target.value)}
              placeholder="base0.example.com:51820"
            />
          </Field>
          <Field label="Allowed IPs">
            <Input
              mono
              value={allowedIps}
              onChange={(e) => setAllowedIps(e.target.value)}
              placeholder="10.80.0.0/16"
            />
          </Field>
          <Field label="Persistent keepalive" error={keepaliveError}>
            <Input
              mono
              type="number"
              value={keepalive}
              onChange={(e) => setKeepalive(e.target.value)}
            />
          </Field>
        </div>
        <div className="flex justify-end mt-4">
          <Button icon={Save} variant="secondary" onClick={handleSave} loading={loading}>
            Save configuration
          </Button>
        </div>
      </CardBody>
    </Card>
  )
}

export function VPNSiteToSite() {
  const { selectedInstanceId } = useInstanceStore()
  const { data: tunnels, isLoading, isError, refetch } = useSiteToSiteStatus(selectedInstanceId!)

  const row = tunnels?.[0]

  const initMutation = useInitializeSiteToSite(selectedInstanceId!)
  const updateMutation = useUpdateVPNServer(selectedInstanceId!)
  const actionMutation = useVPNServerAction(selectedInstanceId!)
  const rotateMutation = useRegenerateVPNClient(selectedInstanceId!, row?.server_id)

  const { data: clients } = useVPNClients(selectedInstanceId!, row?.server_id ?? 0)
  const identityClient = clients?.find((c) => c.public_key) ?? clients?.[0]

  const [initEndpoint, setInitEndpoint] = useState('')
  const [initPeerKey, setInitPeerKey] = useState('')
  const [initAllowedIps, setInitAllowedIps] = useState('')
  const [initLocalAddress, setInitLocalAddress] = useState('')
  const [initKeepalive, setInitKeepalive] = useState('')
  const [endpointError, setEndpointError] = useState('')
  const [keyError, setKeyError] = useState('')
  const [keepaliveError, setKeepaliveError] = useState('')
  const [showStopConfirm, setShowStopConfirm] = useState(false)
  const [showRotateConfirm, setShowRotateConfirm] = useState(false)
  const [rotateResult, setRotateResult] = useState<VPNRegenerateResponse | null>(null)

  const resetInitErrors = () => {
    setEndpointError('')
    setKeyError('')
    setKeepaliveError('')
  }

  const handleInitChange = (field: string, value: string) => {
    resetInitErrors()
    if (field === 'endpoint') setInitEndpoint(value)
    else if (field === 'peerKey') setInitPeerKey(value)
    else if (field === 'allowedIps') setInitAllowedIps(value)
    else if (field === 'localAddress') setInitLocalAddress(value)
    else setInitKeepalive(value)
  }

  const handleInitialize = async () => {
    const endpoint = initEndpoint.trim()
    const peerKey = initPeerKey.trim()
    let valid = true
    if (!endpoint) {
      setEndpointError('Remote endpoint is required')
      valid = false
    } else if (!ENDPOINT_RE.test(endpoint)) {
      setEndpointError('Invalid endpoint — use host or host:port')
      valid = false
    }
    if (!peerKey) {
      setKeyError('Peer public key is required')
      valid = false
    } else if (!WG_KEY_RE.test(peerKey)) {
      setKeyError('Must be a 44-character base64 WireGuard key')
      valid = false
    }
    const keepalive = initKeepalive.trim()
    if (keepalive !== '') {
      const n = Number(keepalive)
      if (!Number.isInteger(n) || n < 0 || n > 65535) {
        setKeepaliveError('Keepalive must be a whole number between 0 and 65535')
        valid = false
      }
    }
    if (!valid) return
    try {
      const res = await initMutation.mutateAsync({
        endpoint,
        peer_public_key: peerKey,
        ...(initAllowedIps.trim() ? { allowed_ips: initAllowedIps.trim() } : {}),
        ...(initLocalAddress.trim() ? { local_address: initLocalAddress.trim() } : {}),
        ...(keepalive !== '' ? { persistent_keepalive: Number(keepalive) } : {}),
      })
      toast.success(res.message)
      setInitEndpoint('')
      setInitPeerKey('')
    } catch (e) {
      toast.error(getErrMsg(e))
    }
  }

  const handleSave = async (body: VPNServerUpdate) => {
    if (!row) return
    try {
      await updateMutation.mutateAsync({ id: row.server_id, ...body })
      toast.success('Tunnel configuration saved')
    } catch (e) {
      toast.error(getErrMsg(e))
    }
  }

  const handleStart = async () => {
    if (!row) return
    try {
      await actionMutation.mutateAsync({ serverId: row.server_id, action: 'start' })
      toast.success(`Tunnel "${row.name}" started`)
    } catch (e) {
      toast.error(getErrMsg(e))
    }
  }

  const handleStop = async () => {
    if (!row) return
    try {
      await actionMutation.mutateAsync({ serverId: row.server_id, action: 'stop' })
      toast.success(`Tunnel "${row.name}" stopped`)
    } catch (e) {
      toast.error(getErrMsg(e))
    }
    setShowStopConfirm(false)
  }

  const handleRotate = async () => {
    if (!identityClient) return
    try {
      const result = await rotateMutation.mutateAsync(identityClient.id)
      setRotateResult(result)
    } catch (e) {
      toast.error(getErrMsg(e))
    }
    setShowRotateConfirm(false)
  }

  if (!selectedInstanceId) {
    return (
      <div>
        <PageHeader
          title="Site-to-Site Tunnels"
          description="WireGuard tunnels to remote networks"
        />
        <Card className="mt-6">
          <div className="flex items-center gap-3 text-on-surface-muted">
            <Info className="h-5 w-5 shrink-0" />
            <p className="text-sm">Select an instance from the top bar to manage its site-to-site tunnels.</p>
          </div>
        </Card>
      </div>
    )
  }

  const live = row?.live ?? null

  return (
    <div>
      <Link
        to="/vpn"
        className="inline-flex items-center gap-1 text-sm text-on-surface-muted hover:text-on-surface mb-4"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to VPN Servers
      </Link>

      <PageHeader
        title="Site-to-Site Tunnels"
        description="WireGuard site-to-site tunnels to remote networks"
      />

      {isError ? (
        <QueryError onRetry={() => refetch()} />
      ) : isLoading ? (
        <div className="space-y-6">
          <Skeleton className="h-28 rounded-card" />
          <SkeletonText lines={6} />
        </div>
      ) : (
        <div className="space-y-6">
          {row ? (
            <>
              <Card>
                <CardBody>
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-primary-subtle rounded-card">
                        <Network className="w-5 h-5 text-primary" />
                      </div>
                      <div>
                        <p className="font-medium text-on-surface">{row.name}</p>
                        <p className="text-xs text-on-surface-muted capitalize">{row.protocol}</p>
                      </div>
                    </div>
                    <TunnelBadge row={row} />
                  </div>

                  <dl className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 text-sm">
                    <div>
                      <dt className="text-on-surface-muted">Remote endpoint</dt>
                      <dd className="font-mono">{row.remote_endpoint ?? '—'}</dd>
                    </div>
                    <div>
                      <dt className="text-on-surface-muted">Local address</dt>
                      <dd className="font-mono">{row.local_address ?? '—'}</dd>
                    </div>
                    <div>
                      <dt className="text-on-surface-muted">Last handshake</dt>
                      <dd className="font-mono">{handshakeAge(live?.latest_handshake_sec)}</dd>
                    </div>
                    <div>
                      <dt className="text-on-surface-muted">Agent</dt>
                      <dd className="capitalize">{row.agent}</dd>
                    </div>
                    <div>
                      <dt className="text-on-surface-muted">Allowed IPs</dt>
                      <dd className="font-mono">{row.allowed_ips ?? '—'}</dd>
                    </div>
                    <div>
                      <dt className="text-on-surface-muted">Keepalive</dt>
                      <dd className="font-mono">{row.persistent_keepalive ?? 25}s</dd>
                    </div>
                    <div>
                      <dt className="text-on-surface-muted">Received</dt>
                      <dd className="font-mono">
                        {live?.transfer_rx != null ? `↓${formatBytes(live.transfer_rx)}` : '—'}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-on-surface-muted">Sent</dt>
                      <dd className="font-mono">
                        {live?.transfer_tx != null ? `↑${formatBytes(live.transfer_tx)}` : '—'}
                      </dd>
                    </div>
                  </dl>

                  <div className="flex flex-wrap items-center gap-3 mt-4">
                    <Button icon={Play} onClick={handleStart} loading={actionMutation.isPending}>
                      Start
                    </Button>
                    <Button
                      variant="secondary"
                      icon={Square}
                      onClick={() => setShowStopConfirm(true)}
                    >
                      Stop
                    </Button>
                    <Button
                      variant="secondary"
                      icon={KeyRound}
                      onClick={() => setShowRotateConfirm(true)}
                      loading={rotateMutation.isPending}
                      disabled={!identityClient}
                      title={
                        identityClient
                          ? undefined
                          : 'Rotating tunnel keys requires a WireGuard client identity'
                      }
                    >
                      Rotate keys
                    </Button>
                    {!identityClient && (
                      <span className="text-xs text-on-surface-muted">
                        A WireGuard client identity is required to rotate keys.
                      </span>
                    )}
                  </div>
                </CardBody>
              </Card>

              <EditForm key={row.server_id} row={row} loading={updateMutation.isPending} onSave={handleSave} />
            </>
          ) : (
            <EmptyState
              icon={Network}
              title="No site-to-site tunnel"
              description="Initialize a site-to-site tunnel below to connect this instance to a remote network."
            />
          )}

          <InitializeForm
            endpoint={initEndpoint}
            peerKey={initPeerKey}
            allowedIps={initAllowedIps}
            localAddress={initLocalAddress}
            keepalive={initKeepalive}
            endpointError={endpointError}
            keyError={keyError}
            keepaliveError={keepaliveError}
            loading={initMutation.isPending}
            onChange={handleInitChange}
            onSubmit={handleInitialize}
          />
        </div>
      )}

      <ConfirmDialog
        open={showStopConfirm}
        onClose={() => setShowStopConfirm(false)}
        onConfirm={handleStop}
        title="Stop Site-to-Site Tunnel"
        message={`Stop "${row?.name}"?`}
        impact="Stopping the tunnel cuts the path to the remote network."
        confirmLabel="Stop"
        variant="warning"
        loading={actionMutation.isPending}
      />

      <ConfirmDialog
        open={showRotateConfirm}
        onClose={() => setShowRotateConfirm(false)}
        onConfirm={handleRotate}
        title="Rotate Tunnel Keys"
        message="Generate a fresh WireGuard keypair for this tunnel's local identity?"
        impact="The new public key must be handed to the remote operator before it takes effect."
        confirmLabel="Rotate keys"
        loading={rotateMutation.isPending}
      />

      <Modal
        open={!!rotateResult}
        onClose={() => setRotateResult(null)}
        title="New tunnel public key"
      >
        <div className="space-y-4">
          <p className="text-sm text-on-surface-muted">
            Hand this public key to the remote (base0) operator so they can update their peer
            configuration. The tunnel reconnects once both sides match.
          </p>
          <div className="flex items-center gap-2">
            <code className="flex-1 font-mono text-sm bg-surface-elevated p-2 rounded-card break-all">
              {rotateResult?.public_key ?? ''}
            </code>
            <IconButton
              icon={Copy}
              label="Copy public key"
              variant="secondary"
              onClick={() => {
                if (rotateResult?.public_key) {
                  void navigator.clipboard.writeText(rotateResult.public_key)
                  toast.success('Public key copied')
                }
              }}
            />
          </div>
          <div className="flex justify-end">
            <Button onClick={() => setRotateResult(null)}>Done</Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
