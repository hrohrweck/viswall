import { useState } from 'react'
import type { InstanceCreate } from '../../types'

interface InstanceCreateFormProps {
  onSubmit: (data: InstanceCreate) => Promise<void>
  onCancel: () => void
  loading: boolean
}

export function InstanceCreateForm({ onSubmit, onCancel, loading }: InstanceCreateFormProps) {
  const [name, setName] = useState('')
  const [hostname, setHostname] = useState('')
  const [error, setError] = useState('')

  const capabilities = ['firewall', 'mail', 'vpn', 'metrics']
  const [selectedCaps, setSelectedCaps] = useState<string[]>([])

  const toggleCap = (cap: string) => {
    setSelectedCaps((prev) =>
      prev.includes(cap) ? prev.filter((c) => c !== cap) : [...prev, cap]
    )
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      await onSubmit({ name, hostname, capabilities: selectedCaps })
    } catch (err: unknown) {
      setError((err as any)?.response?.data?.detail || 'Failed to create instance')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Main Office"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Hostname</label>
        <input
          type="text"
          value={hostname}
          onChange={(e) => setHostname(e.target.value)}
          placeholder="e.g. viswall.example.com"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Capabilities</label>
        <div className="flex flex-wrap gap-2">
          {capabilities.map((cap) => (
            <button
              key={cap}
              type="button"
              onClick={() => toggleCap(cap)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors ${
                selectedCaps.includes(cap)
                  ? 'bg-primary-50 border-primary-300 text-primary-700'
                  : 'bg-white border-gray-300 text-gray-600 hover:bg-gray-50'
              }`}
            >
              {cap}
            </button>
          ))}
        </div>
      </div>

      <div className="flex justify-end gap-3 pt-4">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={loading || !name || !hostname}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
        >
          {loading ? 'Creating...' : 'Create Instance'}
        </button>
      </div>
    </form>
  )
}
