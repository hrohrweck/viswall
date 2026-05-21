import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Mail, Plus, Trash2, Shield, Key, Brain, Users, Globe } from 'lucide-react'
import { useInstanceStore } from '../../stores/instance'
import {
  useMailDomain,
  useMailUsers,
  useCreateMailUser,
  useDeleteMailUser,
  useDeleteMailDomain,
  useRegenerateDkim,
  useGroupwareStatus,
  useEnableGroupware,
  useDisableGroupware,
  useGroupwareStats,
} from '../../hooks/useApi'
import { StatusBadge, Modal, ConfirmDialog, LoadingSpinner, EmptyState, DataTable } from '../../components/ui'
import type { MailUser } from '../../types'
import { formatBytes } from '../../utils/format'
import { MailClassificationView } from './MailClassificationView'

export function MailDomainDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { selectedInstanceId } = useInstanceStore()
  const domainId = Number(id)
  const { data: domain, isLoading } = useMailDomain(selectedInstanceId!, domainId)
  const { data: users } = useMailUsers(selectedInstanceId!, domainId)
  const deleteDomainMutation = useDeleteMailDomain(selectedInstanceId!)
  const createMutation = useCreateMailUser(selectedInstanceId!, domainId)
  const deleteMutation = useDeleteMailUser(selectedInstanceId!, domainId)
  const dkimMutation = useRegenerateDkim(selectedInstanceId!)
  const { data: groupwareStatus } = useGroupwareStatus(domainId)
  const enableGroupware = useEnableGroupware(domainId)
  const disableGroupware = useDisableGroupware(domainId)
  const { data: groupwareStats } = useGroupwareStats(domainId)

  const [showDeleteDomain, setShowDeleteDomain] = useState(false)
  const [showCreateUser, setShowCreateUser] = useState(false)
  const [deleteUserTarget, setDeleteUserTarget] = useState<MailUser | null>(null)
  const [newUsername, setNewUsername] = useState('')
  const [newFullName, setNewFullName] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [activeTab, setActiveTab] = useState<'users' | 'classification' | 'groupware'>('users')

  if (isLoading) return <LoadingSpinner />
  if (!domain) return <p className="text-gray-600">Domain not found.</p>

  const handleCreateUser = async () => {
    await createMutation.mutateAsync({
      username: newUsername,
      full_name: newFullName || undefined,
      password: newPassword || undefined,
    })
    setNewUsername('')
    setNewFullName('')
    setNewPassword('')
    setShowCreateUser(false)
  }

  const handleDeleteDomain = async () => {
    await deleteDomainMutation.mutateAsync(domain.id)
    navigate('/mail')
  }

  const handleDeleteUser = async () => {
    if (deleteUserTarget) {
      await deleteMutation.mutateAsync(deleteUserTarget.id)
      setDeleteUserTarget(null)
    }
  }

  const securityFeatures = [
    { label: 'Spam Filter', enabled: domain.spam_filter_enabled },
    { label: 'Virus Scan', enabled: domain.virus_scan_enabled },
    { label: 'DKIM', enabled: domain.dkim_enabled },
    { label: 'DMARC', enabled: domain.dmarc_enabled },
    { label: 'SPF', enabled: domain.spf_enabled },
    { label: 'LLM Classify', enabled: domain.llm_enabled },
    { label: 'Groupware', enabled: domain.groupware_enabled },
  ]

  const userColumns = [
    {
      key: 'username',
      header: 'User',
      render: (user: MailUser) => (
        <div>
          <p className="font-medium text-gray-900">{user.username}@{domain.domain}</p>
          {user.full_name && <p className="text-xs text-gray-500">{user.full_name}</p>}
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (user: MailUser) => <StatusBadge status={user.enabled ? 'active' : 'inactive'} />,
    },
    {
      key: 'quota',
      header: 'Quota',
      render: (user: MailUser) => (
        <div className="text-sm">
          <div className="w-24 bg-gray-200 rounded-full h-1.5">
            <div
              className="bg-primary-600 h-1.5 rounded-full"
              style={{ width: `${Math.min((user.quota_used / user.quota_bytes) * 100, 100)}%` }}
            />
          </div>
          <span className="text-xs text-gray-500">
            {formatBytes(user.quota_used)} / {formatBytes(user.quota_bytes)}
          </span>
        </div>
      ),
    },
    {
      key: 'forwarding',
      header: 'Forwarding',
      render: (user: MailUser) => (
        <span className="text-sm text-gray-600">
          {user.forward_to.length > 0 ? user.forward_to.join(', ') : '-'}
        </span>
      ),
    },
    {
      key: 'actions',
      header: '',
      render: (user: MailUser) => (
        <button
          onClick={(e) => { e.stopPropagation(); setDeleteUserTarget(user) }}
          className="text-sm text-red-600 hover:text-red-700"
        >
          Delete
        </button>
      ),
    },
  ]

  return (
    <div>
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate('/mail')} className="p-2 hover:bg-gray-100 rounded-lg">
          <ArrowLeft className="w-5 h-5 text-gray-600" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-bold text-gray-900">{domain.domain}</h2>
            <StatusBadge status={domain.enabled ? 'active' : 'inactive'} />
          </div>
        </div>
        <button
          onClick={() => dkimMutation.mutate(domain.id)}
          disabled={dkimMutation.isPending}
          className="flex items-center gap-2 px-3 py-1.5 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm"
        >
          <Key className="w-4 h-4" />
          Regenerate DKIM
        </button>
        <button
          onClick={() => setShowDeleteDomain(true)}
          className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
        >
          <Trash2 className="w-5 h-5" />
        </button>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {securityFeatures.map(({ label, enabled }) => (
          <div key={label} className={`p-4 rounded-lg border ${enabled ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'}`}>
            <div className="flex items-center gap-2">
              <Shield className={`w-4 h-4 ${enabled ? 'text-green-600' : 'text-gray-400'}`} />
              <span className={`text-sm font-medium ${enabled ? 'text-green-700' : 'text-gray-500'}`}>{label}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="border-b border-gray-200 mb-6">
        <nav className="flex gap-6">
          <button
            onClick={() => setActiveTab('users')}
            className={`flex items-center gap-2 pb-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'users'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <Users className="w-4 h-4" />
            Mailboxes ({users?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('classification')}
            className={`flex items-center gap-2 pb-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'classification'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <Brain className="w-4 h-4" />
            Classification
          </button>
          <button
            onClick={() => setActiveTab('groupware')}
            className={`flex items-center gap-2 pb-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'groupware'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <Globe className="w-4 h-4" />
            Groupware
          </button>
        </nav>
      </div>

      {activeTab === 'users' && (
        <>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Mailboxes</h3>
            <button
              onClick={() => setShowCreateUser(true)}
              className="flex items-center gap-2 px-3 py-1.5 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm"
            >
              <Plus className="w-4 h-4" />
              Add Mailbox
            </button>
          </div>

          <DataTable
            columns={userColumns}
            data={users || []}
            keyExtractor={(u) => u.id}
            emptyContent={<EmptyState icon={Mail} title="No mailboxes" description="Create the first mailbox for this domain." actionLabel="Add Mailbox" onAction={() => setShowCreateUser(true)} />}
          />
        </>
      )}

      {activeTab === 'classification' && <MailClassificationView domainId={domainId} />}

      {activeTab === 'groupware' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">SOGo Groupware</h3>
            <div className="flex items-center gap-3">
              <span className={`text-sm font-medium ${domain.groupware_enabled ? 'text-green-600' : 'text-gray-500'}`}>
                {domain.groupware_enabled ? 'Enabled' : 'Disabled'}
              </span>
              <button
                onClick={() => {
                  if (domain.groupware_enabled) {
                    disableGroupware.mutate()
                  } else {
                    enableGroupware.mutate()
                  }
                }}
                disabled={enableGroupware.isPending || disableGroupware.isPending}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  domain.groupware_enabled ? 'bg-primary-600' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    domain.groupware_enabled ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>

          {groupwareStatus?.sogo_url && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-800">
                SOGo is accessible at <a href={groupwareStatus.sogo_url} className="font-medium underline">{groupwareStatus.sogo_url}</a>
              </p>
            </div>
          )}

          {groupwareStats && domain.groupware_enabled && (
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <p className="text-sm text-gray-500">Calendars</p>
                <p className="text-2xl font-semibold text-gray-900">{(groupwareStats.calendars as number) || 0}</p>
              </div>
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <p className="text-sm text-gray-500">Contacts</p>
                <p className="text-2xl font-semibold text-gray-900">{(groupwareStats.contacts as number) || 0}</p>
              </div>
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <p className="text-sm text-gray-500">Active Users</p>
                <p className="text-2xl font-semibold text-gray-900">{(groupwareStats.active_users as number) || 0}</p>
              </div>
            </div>
          )}
        </div>
      )}

      <Modal open={showCreateUser} onClose={() => setShowCreateUser(false)} title="Add Mailbox">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
            <div className="flex">
              <input
                type="text"
                value={newUsername}
                onChange={(e) => setNewUsername(e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-l-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                placeholder="user"
              />
              <span className="px-3 py-2 bg-gray-100 border border-l-0 border-gray-300 rounded-r-lg text-gray-500 text-sm">
                @{domain.domain}
              </span>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
            <input
              type="text"
              value={newFullName}
              onChange={(e) => setNewFullName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              placeholder="Leave empty to auto-generate"
            />
          </div>
          <div className="flex justify-end gap-3">
            <button onClick={() => setShowCreateUser(false)} className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200">Cancel</button>
            <button onClick={handleCreateUser} disabled={!newUsername || createMutation.isPending} className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50">
              {createMutation.isPending ? 'Creating...' : 'Create'}
            </button>
          </div>
        </div>
      </Modal>

      <ConfirmDialog open={!!deleteUserTarget} onClose={() => setDeleteUserTarget(null)} onConfirm={handleDeleteUser} title="Delete Mailbox" message={`Delete "${deleteUserTarget?.username}@${domain.domain}"? All mail data will be permanently lost.`} loading={deleteMutation.isPending} />
      <ConfirmDialog open={showDeleteDomain} onClose={() => setShowDeleteDomain(false)} onConfirm={handleDeleteDomain} title="Delete Domain" message={`Delete "${domain.domain}"? All mailboxes and data will be permanently removed.`} loading={deleteDomainMutation.isPending} />
    </div>
  )
}
