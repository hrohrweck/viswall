import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, ChevronRight, Shield, Zap, Lock, AlertTriangle } from 'lucide-react'

interface ProtocolOption {
  id: string
  name: string
  icon: string
  securityScore: number
  performanceScore: number
  compatibilityScore: number
  description: string
  useCases: string[]
  recommended: boolean
  warning?: string
}

const protocols: ProtocolOption[] = [
  {
    id: 'wireguard',
    name: 'WireGuard',
    icon: '⚡',
    securityScore: 95,
    performanceScore: 98,
    compatibilityScore: 75,
    description: 'Modern, extremely fast and simple VPN protocol. Uses state-of-the-art cryptography.',
    useCases: ['Road warriors', 'Site-to-site', 'Containers', 'Mobile devices'],
    recommended: true,
  },
  {
    id: 'ipsec',
    name: 'IPsec/IKEv2',
    icon: '🔒',
    securityScore: 90,
    performanceScore: 85,
    compatibilityScore: 90,
    description: 'Enterprise standard with native OS support. Excellent for mobile devices.',
    useCases: ['Enterprise', 'Mobile VPN', 'Site-to-site', 'Native clients'],
    recommended: false,
  },
  {
    id: 'openvpn',
    name: 'OpenVPN',
    icon: '🛡️',
    securityScore: 88,
    performanceScore: 75,
    compatibilityScore: 95,
    description: 'Well-tested, flexible, widely supported. Slower but very compatible.',
    useCases: ['Legacy support', 'Complex routing', 'Bridge mode'],
    recommended: false,
  },
  {
    id: 'l2tp',
    name: 'L2TP/IPsec',
    icon: '📡',
    securityScore: 60,
    performanceScore: 70,
    compatibilityScore: 98,
    description: 'Widely supported legacy protocol. Requires IPsec for security.',
    useCases: ['Legacy clients', 'No custom software needed'],
    recommended: false,
  },
  {
    id: 'pptp',
    name: 'PPTP',
    icon: '⚠️',
    securityScore: 20,
    performanceScore: 80,
    compatibilityScore: 100,
    description: 'DEPRECATED - Insecure protocol. Only for legacy compatibility.',
    useCases: ['Legacy systems only'],
    recommended: false,
    warning: 'Not recommended for production use',
  },
]

export function VPNCreate() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [selectedProtocol, setSelectedProtocol] = useState('')
  const [config, setConfig] = useState({
    name: '',
    network_cidr: '10.200.0.0/24',
    listen_port: '',
    dns_servers: ['1.1.1.1', '1.0.0.1'],
    internet_redirect: true,
  })

  const handleProtocolSelect = (protocolId: string) => {
    setSelectedProtocol(protocolId)
    // Set default port based on protocol
    const defaultPorts: Record<string, string> = {
      wireguard: '51820',
      ipsec: '500,4500',
      openvpn: '1194',
      l2tp: '500,4500,1701',
      pptp: '1723',
    }
    setConfig(prev => ({ ...prev, listen_port: defaultPorts[protocolId] }))
  }

  const renderProtocolSelection = () => (
    <div className="space-y-4">
      <p className="text-gray-600 mb-4">Select the VPN protocol for your new server:</p>
      
      {protocols.map((protocol) => (
        <button
          key={protocol.id}
          onClick={() => handleProtocolSelect(protocol.id)}
          className={`w-full p-4 border-2 rounded-lg text-left transition-all ${
            selectedProtocol === protocol.id
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-200 hover:border-gray-300'
          }`}
        >
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-4">
              <span className="text-3xl">{protocol.icon}</span>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-gray-900">{protocol.name}</h3>
                  {protocol.recommended && (
                    <span className="px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded-full">
                      Recommended
                    </span>
                  )}
                  {protocol.warning && (
                    <span className="px-2 py-0.5 bg-red-100 text-red-800 text-xs rounded-full flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" />
                      {protocol.warning}
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-600 mt-1">{protocol.description}</p>
                
                <div className="flex gap-4 mt-2">
                  <span className="text-xs text-gray-500">Security: {protocol.securityScore}/100</span>
                  <span className="text-xs text-gray-500">Performance: {protocol.performanceScore}/100</span>
                </div>
                
                <div className="flex flex-wrap gap-2 mt-2">
                  {protocol.useCases.map((useCase) => (
                    <span key={useCase} className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded">
                      {useCase}
                    </span>
                  ))}
                </div>
              </div>
            </div>
            
            {selectedProtocol === protocol.id && (
              <Zap className="w-5 h-5 text-primary-600" />
            )}
          </div>
        </button>
      ))}
    </div>
  )

  const renderConfiguration = () => (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Server Name
        </label>
        <input
          type="text"
          value={config.name}
          onChange={(e) => setConfig({ ...config, name: e.target.value })}
          placeholder="e.g., Main Office VPN"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Network CIDR
          </label>
          <input
            type="text"
            value={config.network_cidr}
            onChange={(e) => setConfig({ ...config, network_cidr: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
          <p className="text-xs text-gray-500 mt-1">VPN client IP range</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Listen Port
          </label>
          <input
            type="text"
            value={config.listen_port}
            onChange={(e) => setConfig({ ...config, listen_port: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
          <p className="text-xs text-gray-500 mt-1">Comma-separated for multiple</p>
        </div>
      </div>

      <div>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={config.internet_redirect}
            onChange={(e) => setConfig({ ...config, internet_redirect: e.target.checked })}
            className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
          />
          <span className="text-sm text-gray-700">Redirect all client traffic through VPN</span>
        </label>
      </div>
    </div>
  )

  return (
    <div>
      <button
        onClick={() => navigate('/vpn')}
        className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to VPN
      </button>

      <div className="flex items-center gap-4 mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Create VPN Server</h2>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <span className={step >= 1 ? 'text-primary-600 font-medium' : ''}>Protocol</span>
          <ChevronRight className="w-4 h-4" />
          <span className={step >= 2 ? 'text-primary-600 font-medium' : ''}>Configuration</span>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        {step === 1 && renderProtocolSelection()}
        {step === 2 && renderConfiguration()}

        <div className="flex justify-between mt-8 pt-6 border-t border-gray-200">
          {step > 1 ? (
            <button
              onClick={() => setStep(step - 1)}
              className="px-4 py-2 text-gray-700 hover:text-gray-900"
            >
              Back
            </button>
          ) : (
            <div />
          )}

          {step < 2 ? (
            <button
              onClick={() => setStep(step + 1)}
              disabled={!selectedProtocol}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Continue
            </button>
          ) : (
            <button
              onClick={() => {
                // Submit form
                navigate('/vpn')
              }}
              disabled={!config.name}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              Create Server
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
