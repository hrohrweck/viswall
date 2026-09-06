import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shield, Zap, Globe, Smartphone, Check } from 'lucide-react'
import { useInstanceStore } from '../../stores/instance'
import { useCreateVPNServer } from '../../hooks/useApi'
import { VPNProtocol } from '../../types'
import type { VPNServerCreate } from '../../types'
import {
  PageHeader,
  Field,
  Input,
  Button,
  Card,
  CardBody,
  toast,
} from '../../components/ui'
import { cn, getErrMsg } from '../../lib/utils'

/* ------------------------------------------------------------------ */
/*  Static color map — NO template classNames anywhere in this file    */
/* ------------------------------------------------------------------ */

const colorMap: Record<string, { icon: string; bar: string }> = {
  green: { icon: 'text-green-600', bar: 'bg-green-500' },
  blue: { icon: 'text-blue-600', bar: 'bg-blue-500' },
  yellow: { icon: 'text-yellow-600', bar: 'bg-yellow-500' },
  orange: { icon: 'text-orange-600', bar: 'bg-orange-500' },
  red: { icon: 'text-red-600', bar: 'bg-red-500' },
}

/* ------------------------------------------------------------------ */
/*  Protocol definitions                                               */
/* ------------------------------------------------------------------ */

const protocols = [
  {
    id: VPNProtocol.WIREGUARD,
    name: 'WireGuard',
    icon: Zap,
    security: 95,
    performance: 98,
    compatibility: 75,
    recommended: true,
    description: 'Modern, fast, secure. ~4,000 lines of code.',
    color: 'green',
  },
  {
    id: VPNProtocol.IPSEC,
    name: 'IPsec/IKEv2',
    icon: Shield,
    security: 90,
    performance: 85,
    compatibility: 90,
    recommended: false,
    description: 'Enterprise standard with native OS support.',
    color: 'blue',
  },
  {
    id: VPNProtocol.OPENVPN,
    name: 'OpenVPN',
    icon: Globe,
    security: 88,
    performance: 75,
    compatibility: 95,
    recommended: false,
    description: 'Flexible, widely supported, mature.',
    color: 'yellow',
  },
  {
    id: VPNProtocol.L2TP,
    name: 'L2TP/IPsec',
    icon: Smartphone,
    security: 60,
    performance: 70,
    compatibility: 98,
    recommended: false,
    description: 'Legacy compatibility only.',
    color: 'orange',
  },
  {
    id: VPNProtocol.PPTP,
    name: 'PPTP',
    icon: Smartphone,
    security: 20,
    performance: 80,
    compatibility: 100,
    recommended: false,
    description: 'Deprecated. Not recommended.',
    color: 'red',
    warning: 'This protocol has known security vulnerabilities.',
  },
]

/* ------------------------------------------------------------------ */
/*  Step indicator                                                     */
/* ------------------------------------------------------------------ */

function StepIndicator({ current, total }: { current: number; total: number }) {
  return (
    <div className="flex items-center gap-2 mb-8">
      {Array.from({ length: total }, (_, i) => {
        const step = i + 1
        const state = step < current ? 'done' : step === current ? 'current' : 'upcoming'
        return (
          <div key={step} className="flex items-center gap-2">
            <div
              className={cn(
                'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium',
                state === 'done' && 'bg-primary text-primary-fg',
                state === 'current' && 'border-2 border-primary text-primary',
                state === 'upcoming' && 'border border-border text-on-surface-muted',
              )}
            >
              {state === 'done' ? <Check className="w-4 h-4" /> : step}
            </div>
            {step < total && (
              <div
                className={cn(
                  'w-12 h-0.5',
                  state === 'done' ? 'bg-primary' : 'bg-border',
                )}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  VPNCreate                                                          */
/* ------------------------------------------------------------------ */

export function VPNCreate() {
  const navigate = useNavigate()
  const { selectedInstanceId } = useInstanceStore()
  const createMutation = useCreateVPNServer(selectedInstanceId!)

  const [step, setStep] = useState(1)
  const [protocol, setProtocol] = useState<VPNProtocol | null>(null)
  const [name, setName] = useState('')
  const [networkCidr, setNetworkCidr] = useState('10.200.0.0/24')
  const [listenPort, setListenPort] = useState('51820')
  const [dnsServers, setDnsServers] = useState('1.1.1.1, 1.0.0.1')

  const handleCreate = async () => {
    if (!protocol || !selectedInstanceId) return
    try {
      const payload: VPNServerCreate = {
        name,
        protocol,
        network_cidr: networkCidr,
        listen_port: Number(listenPort),
        dns_servers: dnsServers.split(',').map((s) => s.trim()),
      }
      const server = await createMutation.mutateAsync(payload)
      toast.success(`VPN server "${name}" created`)
      navigate(`/vpn/servers/${server.id}`)
    } catch (e) {
      toast.error(getErrMsg(e))
    }
  }

  return (
    <div>
      <PageHeader title="New VPN Server" description="Create a VPN server for your instance" />
      <StepIndicator current={step} total={2} />

      {/* ── Step 1: Protocol ── */}
      {step === 1 && (
        <div>
          <h3 className="text-lg font-semibold text-on-surface mb-4">Choose Protocol</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {protocols.map((p) => {
              const Icon = p.icon
              const colors = colorMap[p.color] ?? colorMap.blue
              return (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => {
                    setProtocol(p.id)
                    if (p.id === VPNProtocol.WIREGUARD) setListenPort('51820')
                    else if (p.id === VPNProtocol.OPENVPN) setListenPort('1194')
                    else setListenPort('500')
                  }}
                  className={cn(
                    'relative p-4 rounded-card border-2 text-left transition-colors',
                    protocol === p.id
                      ? 'border-primary bg-primary-subtle'
                      : 'border-border hover:border-on-surface-muted',
                  )}
                >
                  {p.recommended && (
                    <span className="absolute top-2 right-2 px-2 py-0.5 bg-success-subtle text-success text-xs rounded-full">
                      Recommended
                    </span>
                  )}
                  <div className="flex items-center gap-3 mb-2">
                    <Icon className={cn('w-5 h-5', colors.icon)} />
                    <span className="font-semibold text-on-surface">{p.name}</span>
                  </div>
                  <p className="text-sm text-on-surface-muted mb-3">{p.description}</p>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 text-xs">
                      <span className="w-16 text-on-surface-muted">Security</span>
                      <div className="flex-1 h-1.5 bg-surface-elevated rounded">
                        <div className={cn('h-full rounded', colors.bar)} style={{ width: `${p.security}%` }} />
                      </div>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      <span className="w-16 text-on-surface-muted">Speed</span>
                      <div className="flex-1 h-1.5 bg-surface-elevated rounded">
                        <div className={cn('h-full rounded', colors.bar)} style={{ width: `${p.performance}%` }} />
                      </div>
                    </div>
                  </div>
                  {p.warning && (
                    <p className="mt-2 text-xs text-danger bg-danger-subtle p-2 rounded-card">{p.warning}</p>
                  )}
                </button>
              )
            })}
          </div>
          <div className="flex justify-end mt-6">
            <Button onClick={() => setStep(2)} disabled={!protocol}>
              Continue
            </Button>
          </div>
        </div>
      )}

      {/* ── Step 2: Configuration ── */}
      {step === 2 && (
        <div>
          <h3 className="text-lg font-semibold text-on-surface mb-4">Configuration</h3>
          <div className="max-w-lg space-y-4">
            <Field label="Server Name">
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Main Office VPN"
              />
            </Field>
            <div className="grid grid-cols-2 gap-4">
              <Field label="Network CIDR">
                <Input
                  mono
                  value={networkCidr}
                  onChange={(e) => setNetworkCidr(e.target.value)}
                />
              </Field>
              <Field label="Listen Port">
                <Input
                  mono
                  type="number"
                  value={listenPort}
                  onChange={(e) => setListenPort(e.target.value)}
                />
              </Field>
            </div>
            <Field label="DNS Servers">
              <Input
                mono
                value={dnsServers}
                onChange={(e) => setDnsServers(e.target.value)}
                placeholder="1.1.1.1, 1.0.0.1"
              />
            </Field>
          </div>
          <div className="flex justify-between mt-6">
            <Button variant="secondary" onClick={() => setStep(1)}>
              Back
            </Button>
            <Button onClick={handleCreate} disabled={!name} loading={createMutation.isPending}>
              Create VPN Server
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
