import { Link } from 'react-router-dom'
import { Plus, Mail, Shield, AlertTriangle, CheckCircle } from 'lucide-react'
import { useState } from 'react'
import { useInstanceStore } from '../../stores/instance'
import { useMailDomains, useDeleteMailDomain } from '../../hooks/useApi'
import { InstanceSelector, StatusBadge, ConfirmDialog, EmptyState, LoadingSpinner } from '../../components/ui'
import type { MailDomain } from '../../types'

export function MailDomains() {
  const { selectedInstanceId } = useInstanceStore()
  const { data: domains, isLoading } = useMailDomains(selectedInstanceId!)
  const deleteMutation = useDeleteMailDomain(selectedInstanceId!)
  const [deleteTarget, setDeleteTarget] = useState<MailDomain | null>(null)

  const handleDelete = async () => {
    if (deleteTarget) {
      await deleteMutation.mutateAsync(deleteTarget.id)
      setDeleteTarget(null)
    }
  }

  if (!selectedInstanceId) {
    return (
      <div>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Mail Domains</h2>
            <p className="text-gray-600 mt-1">Manage email domains, users, and security settings</p>
          </div>
        </div>
        <EmptyState icon={Mail} title="Select an Instance" description="Choose an instance to manage mail domains." />
        <div className="mt-4"><InstanceSelector /></div>
      </div>
    )
  }

  if (isLoading) return <LoadingSpinner />

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Mail Domains</h2>
            <p className="text-gray-600 mt-1">Manage email domains, users, and security settings</p>
          </div>
          <InstanceSelector />
        </div>
        <Link
          to="/mail/domains/create"
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          <Plus className="w-5 h-5" />
          Add Domain
        </Link>
      </div>

      {domains && domains.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg"><Mail className="w-5 h-5 text-blue-600" /></div>
              <div><p className="text-sm text-gray-600">Total Domains</p><p className="text-2xl font-bold">{domains.length}</p></div>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg"><CheckCircle className="w-5 h-5 text-green-600" /></div>
              <div><p className="text-sm text-gray-600">Active</p><p className="text-2xl font-bold">{domains.filter((d) => d.enabled).length}</p></div>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg"><Shield className="w-5 h-5 text-purple-600" /></div>
              <div><p className="text-sm text-gray-600">Spam Filter</p><p className="text-2xl font-bold">{domains.filter((d) => d.spam_filter_enabled).length}</p></div>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-100 rounded-lg"><AlertTriangle className="w-5 h-5 text-red-600" /></div>
              <div><p className="text-sm text-gray-600">Antivirus</p><p className="text-2xl font-bold">{domains.filter((d) => d.virus_scan_enabled).length}</p></div>
            </div>
          </div>
        </div>
      )}

      {domains && domains.length > 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="divide-y divide-gray-200">
            {domains.map((domain) => (
              <Link
                key={domain.id}
                to={`/mail/domains/${domain.id}`}
                className="p-6 hover:bg-gray-50 flex items-center justify-between group"
              >
                <div className="flex items-center gap-4">
                  <div className={`p-3 rounded-lg ${domain.enabled ? 'bg-blue-100' : 'bg-gray-100'}`}>
                    <Mail className={`w-6 h-6 ${domain.enabled ? 'text-blue-600' : 'text-gray-400'}`} />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{domain.domain}</h3>
                    <div className="flex items-center gap-3 text-sm text-gray-600 mt-1">
                      {domain.spam_filter_enabled && <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs">Spam Filter</span>}
                      {domain.virus_scan_enabled && <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded text-xs">Antivirus</span>}
                      {domain.dkim_enabled && <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs">DKIM</span>}
                      {domain.dmarc_enabled && <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">DMARC</span>}
                      {domain.llm_enabled && <span className="px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded text-xs">AI Classify</span>}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); setDeleteTarget(domain) }}
                    className="text-sm text-red-600 hover:text-red-700 opacity-0 group-hover:opacity-100"
                  >
                    Delete
                  </button>
                  <StatusBadge status={domain.enabled ? 'active' : 'inactive'} />
                </div>
              </Link>
            ))}
          </div>
        </div>
      ) : (
        <EmptyState
          icon={Mail}
          title="No mail domains"
          description="Add your first email domain to get started."
          actionLabel="Add Domain"
          actionTo="/mail/domains/create"
        />
      )}

      <ConfirmDialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Delete Domain"
        message={`Delete "${deleteTarget?.domain}"? All associated users and mail data will be removed.`}
        loading={deleteMutation.isPending}
      />
    </div>
  )
}
