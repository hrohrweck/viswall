import { useState } from 'react'
import type { FirewallRuleCreate, FirewallRuleUpdate } from '../../types'
import { FirewallAction } from '../../types'

interface FirewallRuleFormProps {
  initial?: Partial<FirewallRuleCreate & { id: number }>
  onSubmit: (data: FirewallRuleCreate | FirewallRuleUpdate) => Promise<void>
  onCancel: () => void
  loading: boolean
}

export function FirewallRuleForm({ initial, onSubmit, onCancel, loading }: FirewallRuleFormProps) {
  const [name, setName] = useState(initial?.name || '')
  const [description, setDescription] = useState(initial?.description || '')
  const [sourceType, setSourceType] = useState(initial?.source_type || 'any')
  const [sourceValue, setSourceValue] = useState(initial?.source_value || '')
  const [destType, setDestType] = useState(initial?.dest_type || 'any')
  const [destValue, setDestValue] = useState(initial?.dest_value || '')
  const [protocol, setProtocol] = useState(initial?.service_protocol || 'tcp')
  const [ports, setPorts] = useState(initial?.service_ports || '')
  const [action, setAction] = useState<FirewallAction>(initial?.action || FirewallAction.ACCEPT)
  const [logEnabled, setLogEnabled] = useState(initial?.log_enabled || false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      await onSubmit({
        name,
        description: description || undefined,
        source_type: sourceType,
        source_value: sourceType !== 'any' ? sourceValue : undefined,
        dest_type: destType,
        dest_value: destType !== 'any' ? destValue : undefined,
        service_protocol: protocol,
        service_ports: ports || undefined,
        action,
        log_enabled: logEnabled,
      })
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save rule')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Rule Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Source Type</label>
          <select
            value={sourceType}
            onChange={(e) => setSourceType(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="any">Any</option>
            <option value="ip">IP Address</option>
            <option value="network">Network (CIDR)</option>
            <option value="interface">Interface</option>
          </select>
        </div>
        {sourceType !== 'any' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Source Value</label>
            <input
              type="text"
              value={sourceValue}
              onChange={(e) => setSourceValue(e.target.value)}
              placeholder={sourceType === 'network' ? '10.0.0.0/8' : 'eth0'}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Destination Type</label>
          <select
            value={destType}
            onChange={(e) => setDestType(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="any">Any</option>
            <option value="ip">IP Address</option>
            <option value="network">Network (CIDR)</option>
            <option value="interface">Interface</option>
          </select>
        </div>
        {destType !== 'any' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Destination Value</label>
            <input
              type="text"
              value={destValue}
              onChange={(e) => setDestValue(e.target.value)}
              placeholder={destType === 'network' ? '192.168.1.0/24' : 'eth1'}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
        )}
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Protocol</label>
          <select
            value={protocol}
            onChange={(e) => setProtocol(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="tcp">TCP</option>
            <option value="udp">UDP</option>
            <option value="icmp">ICMP</option>
            <option value="any">Any</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Ports</label>
          <input
            type="text"
            value={ports}
            onChange={(e) => setPorts(e.target.value)}
            placeholder="e.g. 80, 443 or 1000-2000"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Action</label>
          <select
            value={action}
            onChange={(e) => setAction(e.target.value as FirewallAction)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="accept">Accept</option>
            <option value="drop">Drop</option>
            <option value="reject">Reject</option>
          </select>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="logEnabled"
          checked={logEnabled}
          onChange={(e) => setLogEnabled(e.target.checked)}
          className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
        />
        <label htmlFor="logEnabled" className="text-sm text-gray-700">Log matched packets</label>
      </div>

      <div className="flex justify-end gap-3 pt-4">
        <button type="button" onClick={onCancel} className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200">
          Cancel
        </button>
        <button type="submit" disabled={loading} className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50">
          {loading ? 'Saving...' : 'Save Rule'}
        </button>
      </div>
    </form>
  )
}
