import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Copy, ExternalLink } from 'lucide-react'
import { useInstance, useDeleteInstance } from '../hooks/useApi'
import { StatusBadge, ConfirmDialog, LoadingSpinner } from '../components/ui'
import { useState } from 'react'
import { formatDistanceToNow } from 'date-fns'

export function InstanceDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const instanceId = Number(id)
  const { data: instance, isLoading } = useInstance(instanceId)
  const deleteMutation = useDeleteInstance()
  const [showDelete, setShowDelete] = useState(false)
  const [copied, setCopied] = useState(false)

  if (isLoading) return <LoadingSpinner />
  if (!instance) return <p className="text-gray-600">Instance not found.</p>

  const copyApiKey = () => {
    navigator.clipboard.writeText(instance.api_endpoint)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDelete = async () => {
    await deleteMutation.mutateAsync(instance.id)
    navigate('/instances')
  }

  return (
    <div>
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate('/instances')} className="p-2 hover:bg-gray-100 rounded-lg">
          <ArrowLeft className="w-5 h-5 text-gray-600" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-bold text-gray-900">{instance.name}</h2>
            <StatusBadge status={instance.status} />
          </div>
          <p className="text-sm text-gray-500">{instance.hostname}</p>
        </div>
        <button
          onClick={() => setShowDelete(true)}
          className="px-4 py-2 text-red-600 border border-red-200 rounded-lg hover:bg-red-50"
        >
          Delete
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Overview</h3>
          <dl className="space-y-3">
            <div className="flex justify-between">
              <dt className="text-sm text-gray-500">Hostname</dt>
              <dd className="text-sm font-medium text-gray-900">{instance.hostname}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-sm text-gray-500">Status</dt>
              <dd><StatusBadge status={instance.status} /></dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-sm text-gray-500">Last Seen</dt>
              <dd className="text-sm text-gray-900">
                {instance.last_seen
                  ? formatDistanceToNow(new Date(instance.last_seen), { addSuffix: true })
                  : 'Never'}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-sm text-gray-500">Created</dt>
              <dd className="text-sm text-gray-900">
                {new Date(instance.created_at).toLocaleDateString()}
              </dd>
            </div>
          </dl>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Connection</h3>
          <dl className="space-y-3">
            <div>
              <dt className="text-sm text-gray-500 mb-1">API Endpoint</dt>
              <dd className="flex items-center gap-2">
                <code className="text-sm bg-gray-100 px-2 py-1 rounded flex-1 truncate">
                  {instance.api_endpoint}
                </code>
                <button onClick={copyApiKey} className="p-1.5 hover:bg-gray-100 rounded" title="Copy">
                  <Copy className="w-4 h-4 text-gray-400" />
                </button>
                {copied && <span className="text-xs text-green-600">Copied!</span>}
              </dd>
            </div>
          </dl>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Capabilities</h3>
          <div className="flex flex-wrap gap-2">
            {instance.capabilities.length > 0 ? (
              instance.capabilities.map((cap) => (
                <span
                  key={cap}
                  className="px-3 py-1.5 bg-primary-50 text-primary-700 rounded-lg text-sm font-medium"
                >
                  {cap}
                </span>
              ))
            ) : (
              <p className="text-gray-400 text-sm">No capabilities assigned</p>
            )}
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Links</h3>
          <div className="space-y-2">
            <a
              href={`/firewall?instance=${instance.id}`}
              className="flex items-center gap-2 p-3 rounded-lg hover:bg-gray-50 text-sm text-gray-700"
            >
              <ExternalLink className="w-4 h-4" />
              Firewall Rules
            </a>
            <a
              href={`/vpn?instance=${instance.id}`}
              className="flex items-center gap-2 p-3 rounded-lg hover:bg-gray-50 text-sm text-gray-700"
            >
              <ExternalLink className="w-4 h-4" />
              VPN Servers
            </a>
            <a
              href={`/mail?instance=${instance.id}`}
              className="flex items-center gap-2 p-3 rounded-lg hover:bg-gray-50 text-sm text-gray-700"
            >
              <ExternalLink className="w-4 h-4" />
              Mail Domains
            </a>
          </div>
        </div>
      </div>

      <ConfirmDialog
        open={showDelete}
        onClose={() => setShowDelete(false)}
        onConfirm={handleDelete}
        title="Delete Instance"
        message={`Are you sure you want to delete "${instance.name}"? This will remove all associated rules and configuration.`}
        loading={deleteMutation.isPending}
      />
    </div>
  )
}
