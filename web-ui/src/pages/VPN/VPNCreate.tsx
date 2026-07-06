import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shield, Zap, Globe, Smartphone } from 'lucide-react'
import { useInstanceStore } from '../../stores/instance'
import { useCreateVPNServer } from '../../hooks/useApi'
import { VPNProtocol } from '../../types'
import type { VPNServerCreate } from '../../types'

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
  const [error, setError] = useState('')

  const handleCreate = async () => {
    if (!protocol || !selectedInstanceId) return
    setError('')
    try {
      const payload: VPNServerCreate = {
        name,
        protocol,
        network_cidr: networkCidr,
        listen_port: Number(listenPort),
        dns_servers: dnsServers.split(',').map((s) => s.trim()),
      }
      const server = await createMutation.mutateAsync(payload)
      navigate(`/vpn/servers/${server.id}`)
    } catch (err: unknown) {
      setError((err as any)?.response?.data?.detail || 'Failed to create VPN server')
    }
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6 dark:text-white">New VPN Server</h2>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm dark:bg-red-950/20 dark:border-red-900 dark:text-red-400">{error}</div>
      )}

      {step === 1 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4 dark:text-white">1. Choose Protocol</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {protocols.map((p) => (
              <button
                key={p.id}
                onClick={() => {
                  setProtocol(p.id)
                  if (p.id === VPNProtocol.WIREGUARD) setListenPort('51820')
                  else if (p.id === VPNProtocol.OPENVPN) setListenPort('1194')
                  else setListenPort('500')
                }}
                className={`relative p-4 rounded-lg border-2 text-left transition-colors ${
                  protocol === p.id ? 'border-primary-500 bg-primary-50 dark:bg-primary-950/30' : 'border-gray-200 hover:border-gray-300 dark:border-gray-700 dark:hover:border-gray-600'
                }`}
              >
                {p.recommended && (
                  <span className="absolute top-2 right-2 px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full dark:bg-green-950/30 dark:text-green-400">
                    Recommended
                  </span>
                )}
                <div className="flex items-center gap-3 mb-2">
                  <p.icon className={`w-5 h-5 text-${p.color}-600 dark:text-${p.color}-400`} />
                  <span className="font-semibold text-gray-900 dark:text-white">{p.name}</span>
                </div>
                <p className="text-sm text-gray-600 mb-3 dark:text-gray-400">{p.description}</p>
                <div className="space-y-1">
                  <div className="flex items-center gap-2 text-xs">
                    <span className="w-16 text-gray-500 dark:text-gray-400">Security</span>
                    <div className="flex-1 h-1.5 bg-gray-200 rounded dark:bg-gray-800">
                      <div className={`h-full bg-${p.color}-500 rounded`} style={{ width: `${p.security}%` }} />
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="w-16 text-gray-500 dark:text-gray-400">Speed</span>
                    <div className="flex-1 h-1.5 bg-gray-200 rounded dark:bg-gray-800">
                      <div className={`h-full bg-${p.color}-500 rounded`} style={{ width: `${p.performance}%` }} />
                    </div>
                  </div>
                </div>
                {p.warning && (
                  <p className="mt-2 text-xs text-red-600 bg-red-50 p-2 rounded dark:bg-red-950/30 dark:text-red-400">{p.warning}</p>
                )}
              </button>
            ))}
          </div>
          <div className="flex justify-end mt-6">
            <button onClick={() => setStep(2)} disabled={!protocol} className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50">
              Next
            </button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4 dark:text-white">2. Configuration</h3>
          <div className="max-w-lg space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">Server Name</label>
              <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Main Office VPN" className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white" required />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">Network CIDR</label>
                <input type="text" value={networkCidr} onChange={(e) => setNetworkCidr(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">Listen Port</label>
                <input type="number" value={listenPort} onChange={(e) => setListenPort(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">DNS Servers</label>
              <input type="text" value={dnsServers} onChange={(e) => setDnsServers(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white" />
            </div>
          </div>
          <div className="flex justify-between mt-6">
            <button onClick={() => setStep(1)} className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700">Back</button>
            <button onClick={handleCreate} disabled={!name || createMutation.isPending} className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50">
              {createMutation.isPending ? 'Creating...' : 'Create VPN Server'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
