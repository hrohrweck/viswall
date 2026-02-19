import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Mail, Shield, AlertTriangle, CheckCircle } from 'lucide-react'

interface MailDomain {
  id: number
  domain: string
  enabled: boolean
  user_count: number
  spam_filter_enabled: boolean
  virus_scan_enabled: boolean
  dkim_enabled: boolean
  dmarc_enabled: boolean
  llm_enabled: boolean
}

const mockDomains: MailDomain[] = [
  {
    id: 1,
    domain: 'example.com',
    enabled: true,
    user_count: 25,
    spam_filter_enabled: true,
    virus_scan_enabled: true,
    dkim_enabled: true,
    dmarc_enabled: true,
    llm_enabled: false,
  },
  {
    id: 2,
    domain: 'company.org',
    enabled: true,
    user_count: 150,
    spam_filter_enabled: true,
    virus_scan_enabled: true,
    dkim_enabled: true,
    dmarc_enabled: false,
    llm_enabled: true,
  },
]

export function MailDomains() {
  const [domains] = useState(mockDomains)
  const [selectedInstance] = useState(1)

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Mail Domains</h2>
          <p className="text-gray-600 mt-1">Manage email domains, users, and security settings</p>
        </div>
        <Link
          to="/mail/domains/create"
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          <Plus className="w-5 h-5" />
          Add Domain
        </Link>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Mail className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Domains</p>
              <p className="text-2xl font-bold">{domains.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Active Users</p>
              <p className="text-2xl font-bold">{domains.reduce((acc, d) => acc + d.user_count, 0)}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Shield className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Spam Blocked</p>
              <p className="text-2xl font-bold">1,247</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-100 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Viruses Blocked</p>
              <p className="text-2xl font-bold">23</p>
            </div>
          </div>
        </div>
      </div>

      {/* Domains List */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        {domains.length === 0 ? (
          <div className="p-12 text-center">
            <Mail className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No mail domains</h3>
            <p className="text-gray-600 mb-6">Add your first email domain to get started.</p>
            <Link
              to="/mail/domains/create"
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
            >
              Add Domain
            </Link>
          </div>
        ) : (
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
                      <span>{domain.user_count} users</span㸾
                      {domain.spam_filter_enabled && (
                        <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs">
                          Spam Filter
                        </span>
                      )}
                      {domain.virus_scan_enabled && (
                        <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded text-xs">
                          Antivirus
                        </span>
                      )}
                      {domain.dkim_enabled && (
                        <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs">
                          DKIM
                        </span>
                      )}
                      {domain.llm_enabled && (
                        <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">
                          AI Classify
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                
                <span className={`px-3 py-1 text-sm rounded-full ${
                  domain.enabled
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {domain.enabled ? 'Active' : 'Disabled'}
                </span>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
