import { useState, useEffect } from 'react'
import {
  Settings as SettingsIcon,
  Save,
  RefreshCw,
  Bot,
  Server,
  Palette,
  Shield,
  Trash2,
  Plug,
} from 'lucide-react'
import {
  useLLMConfig,
  useUpdateLLMConfig,
  useLDAPConfig,
  useUpdateLDAPConfig,
  useDeleteLDAPConfig,
  useTestLDAPConnection,
} from '../hooks/useApi'
import { useAuthStore } from '../stores/auth'
import { useThemeStore, Theme } from '../stores/theme'
import { LoadingSpinner, EmptyState } from '../components/ui'
import type { LLMConfig, LDAPConfig } from '../types'

export function Settings() {
  const { user } = useAuthStore()
  const isAdmin = user?.role === 'admin' || user?.role === 'superadmin'

  const { data: llmConfig, isLoading: llmLoading } = useLLMConfig()
  const updateLLM = useUpdateLLMConfig()

  const { data: ldapConfig, isLoading: ldapLoading } = useLDAPConfig()
  const updateLDAP = useUpdateLDAPConfig()
  const deleteLDAP = useDeleteLDAPConfig()
  const testLDAP = useTestLDAPConnection()

  const { theme, setTheme } = useThemeStore()

  const [llmForm, setLlmForm] = useState<LLMConfig | null>(null)
  const [ldapForm, setLdapForm] = useState<LDAPConfig | null>(null)
  const [saved, setSaved] = useState(false)
  const [ldapSaved, setLdapSaved] = useState(false)
  const [ldapTestResult, setLdapTestResult] = useState<string | null>(null)

  useEffect(() => {
    if (llmConfig) {
      setLlmForm(llmConfig)
    }
  }, [llmConfig])

  useEffect(() => {
    if (ldapConfig) {
      setLdapForm(ldapConfig)
    } else if (ldapConfig === null) {
      // Set default empty form
      setLdapForm({
        server_url: '',
        bind_dn: '',
        bind_password: '',
        base_dn: '',
        user_filter: '(objectClass=person)',
      })
    }
  }, [ldapConfig])

  const handleSaveLLM = async () => {
    if (!llmForm) return
    await updateLLM.mutateAsync(llmForm)
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  const handleSaveLDAP = async () => {
    if (!ldapForm) return
    await updateLDAP.mutateAsync(ldapForm)
    setLdapSaved(true)
    setTimeout(() => setLdapSaved(false), 3000)
  }

  const handleTestLDAP = async () => {
    if (!ldapForm) return
    setLdapTestResult(null)
    try {
      const result = await testLDAP.mutateAsync(ldapForm)
      setLdapTestResult(result.message)
    } catch (err: unknown) {
      setLdapTestResult((err as any)?.response?.data?.detail || 'Connection failed')
    }
  }

  const handleDeleteLDAP = async () => {
    if (confirm('Are you sure you want to remove the LDAP configuration?')) {
      await deleteLDAP.mutateAsync()
    }
  }

  if (llmLoading || ldapLoading) return <LoadingSpinner />

  const inputClass =
    'w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white dark:bg-gray-800 dark:border-gray-700 dark:text-white'
  const labelClass = 'block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1'

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Settings</h2>

      {/* Theme Settings */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6 dark:bg-gray-900 dark:border-gray-700">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center gap-3 dark:border-gray-700">
          <Palette className="w-5 h-5 text-primary-600" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Appearance</h3>
        </div>
        <div className="p-6">
          <label className={labelClass}>Theme</label>
          <div className="flex items-center gap-3 mt-2">
            {(['light', 'dark', 'system'] as Theme[]).map((t) => (
              <button
                key={t}
                onClick={() => setTheme(t)}
                className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${
                  theme === t
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700'
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* LLM Configuration */}
      {isAdmin && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6 dark:bg-gray-900 dark:border-gray-700">
          <div className="px-6 py-4 border-b border-gray-200 flex items-center gap-3 dark:border-gray-700">
            <Bot className="w-5 h-5 text-primary-600" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              LLM Configuration
            </h3>
          </div>
          <div className="p-6 space-y-4">
            {llmForm ? (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className={labelClass}>Provider</label>
                    <select
                      value={llmForm.provider}
                      onChange={(e) => setLlmForm({ ...llmForm, provider: e.target.value })}
                      className={inputClass}
                    >
                      <option value="openai">OpenAI</option>
                      <option value="anthropic">Anthropic</option>
                      <option value="local">Local (Ollama)</option>
                    </select>
                  </div>
                  <div>
                    <label className={labelClass}>Model</label>
                    <input
                      type="text"
                      value={llmForm.model}
                      onChange={(e) => setLlmForm({ ...llmForm, model: e.target.value })}
                      className={inputClass}
                      placeholder="gpt-4"
                    />
                  </div>
                </div>

                <div>
                  <label className={labelClass}>API Key</label>
                  <input
                    type="password"
                    value={llmForm.api_key || ''}
                    onChange={(e) => setLlmForm({ ...llmForm, api_key: e.target.value || undefined })}
                    className={inputClass}
                    placeholder="sk-..."
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Leave empty to use environment variable.
                  </p>
                </div>

                <div>
                  <label className={labelClass}>API Base URL (optional)</label>
                  <input
                    type="text"
                    value={llmForm.api_base || ''}
                    onChange={(e) => setLlmForm({ ...llmForm, api_base: e.target.value || undefined })}
                    className={inputClass}
                    placeholder="https://api.openai.com/v1"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className={labelClass}>Temperature ({llmForm.temperature})</label>
                    <input
                      type="range"
                      min={0}
                      max={2}
                      step={0.1}
                      value={llmForm.temperature}
                      onChange={(e) =>
                        setLlmForm({ ...llmForm, temperature: parseFloat(e.target.value) })
                      }
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>Precise</span>
                      <span>Creative</span>
                    </div>
                  </div>
                  <div>
                    <label className={labelClass}>Max Tokens</label>
                    <input
                      type="number"
                      value={llmForm.max_tokens}
                      onChange={(e) =>
                        setLlmForm({ ...llmForm, max_tokens: parseInt(e.target.value) })
                      }
                      className={inputClass}
                      min={1}
                      max={8000}
                    />
                  </div>
                </div>

                <div>
                  <label className={labelClass}>System Prompt</label>
                  <textarea
                    value={llmForm.system_prompt}
                    onChange={(e) => setLlmForm({ ...llmForm, system_prompt: e.target.value })}
                    className={inputClass + ' min-h-[80px]'}
                    rows={3}
                  />
                </div>

                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="auto_classify"
                      checked={llmForm.auto_classify}
                      onChange={(e) =>
                        setLlmForm({ ...llmForm, auto_classify: e.target.checked })
                      }
                      className="w-4 h-4"
                    />
                    <label htmlFor="auto_classify" className="text-sm text-gray-700 dark:text-gray-300">
                      Auto-classify emails
                    </label>
                  </div>
                </div>

                {llmForm.auto_classify && (
                  <div>
                    <label className={labelClass}>
                      Confidence Threshold ({llmForm.confidence_threshold})
                    </label>
                    <input
                      type="range"
                      min={0}
                      max={1}
                      step={0.05}
                      value={llmForm.confidence_threshold}
                      onChange={(e) =>
                        setLlmForm({
                          ...llmForm,
                          confidence_threshold: parseFloat(e.target.value),
                        })
                      }
                      className="w-full"
                    />
                  </div>
                )}

                <div className="flex items-center justify-between pt-4">
                  <div>
                    {saved && (
                      <span className="text-sm text-green-600 font-medium">
                        Configuration saved!
                      </span>
                    )}
                  </div>
                  <button
                    onClick={handleSaveLLM}
                    disabled={updateLLM.isPending}
                    className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm disabled:opacity-50"
                  >
                    <Save className="w-4 h-4" />
                    {updateLLM.isPending ? 'Saving...' : 'Save Configuration'}
                  </button>
                </div>
              </>
            ) : (
              <EmptyState
                icon={Bot}
                title="No Configuration"
                description="Unable to load LLM configuration."
              />
            )}
          </div>
        </div>
      )}

      {/* LDAP / AD Configuration */}
      {isAdmin && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6 dark:bg-gray-900 dark:border-gray-700">
          <div className="px-6 py-4 border-b border-gray-200 flex items-center gap-3 dark:border-gray-700">
            <Shield className="w-5 h-5 text-primary-600" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              LDAP / Active Directory
            </h3>
          </div>
          <div className="p-6 space-y-4">
            {ldapForm ? (
              <>
                <div>
                  <label className={labelClass}>Server URL</label>
                  <input
                    type="text"
                    value={ldapForm.server_url}
                    onChange={(e) => setLdapForm({ ...ldapForm, server_url: e.target.value })}
                    className={inputClass}
                    placeholder="ldap://localhost:389 or ldaps://ad.example.com:636"
                  />
                </div>

                <div>
                  <label className={labelClass}>Bind DN</label>
                  <input
                    type="text"
                    value={ldapForm.bind_dn}
                    onChange={(e) => setLdapForm({ ...ldapForm, bind_dn: e.target.value })}
                    className={inputClass}
                    placeholder="cn=admin,dc=example,dc=com"
                  />
                </div>

                <div>
                  <label className={labelClass}>Bind Password</label>
                  <input
                    type="password"
                    value={ldapForm.bind_password}
                    onChange={(e) => setLdapForm({ ...ldapForm, bind_password: e.target.value })}
                    className={inputClass}
                    placeholder="Service account password"
                  />
                </div>

                <div>
                  <label className={labelClass}>Base DN</label>
                  <input
                    type="text"
                    value={ldapForm.base_dn}
                    onChange={(e) => setLdapForm({ ...ldapForm, base_dn: e.target.value })}
                    className={inputClass}
                    placeholder="dc=example,dc=com"
                  />
                </div>

                <div>
                  <label className={labelClass}>User Filter</label>
                  <input
                    type="text"
                    value={ldapForm.user_filter}
                    onChange={(e) => setLdapForm({ ...ldapForm, user_filter: e.target.value })}
                    className={inputClass}
                    placeholder="(objectClass=person)"
                  />
                </div>

                <div>
                  <label className={labelClass}>Group Filter (optional)</label>
                  <input
                    type="text"
                    value={ldapForm.group_filter || ''}
                    onChange={(e) => setLdapForm({ ...ldapForm, group_filter: e.target.value || undefined })}
                    className={inputClass}
                    placeholder="(objectClass=groupOfNames)"
                  />
                </div>

                {ldapTestResult && (
                  <div
                    className={`p-3 rounded-lg text-sm ${
                      ldapTestResult.toLowerCase().includes('success')
                        ? 'bg-green-50 text-green-700 dark:bg-green-900/20'
                        : 'bg-red-50 text-red-700 dark:bg-red-900/20'
                    }`}
                  >
                    {ldapTestResult}
                  </div>
                )}

                <div className="flex items-center justify-between pt-4">
                  <div className="flex items-center gap-2">
                    {ldapSaved && (
                      <span className="text-sm text-green-600 font-medium">
                        Configuration saved!
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    {ldapConfig && (
                      <button
                        onClick={handleDeleteLDAP}
                        disabled={deleteLDAP.isPending}
                        className="flex items-center gap-2 px-4 py-2 bg-white border border-red-200 text-red-600 rounded-lg hover:bg-red-50 text-sm"
                      >
                        <Trash2 className="w-4 h-4" />
                        Remove
                      </button>
                    )}
                    <button
                      onClick={handleTestLDAP}
                      disabled={testLDAP.isPending}
                      className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 text-sm"
                    >
                      <Plug className="w-4 h-4" />
                      {testLDAP.isPending ? 'Testing...' : 'Test Connection'}
                    </button>
                    <button
                      onClick={handleSaveLDAP}
                      disabled={updateLDAP.isPending}
                      className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm disabled:opacity-50"
                    >
                      <Save className="w-4 h-4" />
                      {updateLDAP.isPending ? 'Saving...' : 'Save'}
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <EmptyState
                icon={Shield}
                title="No Configuration"
                description="Unable to load LDAP configuration."
              />
            )}
          </div>
        </div>
      )}

      {/* System Information */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 dark:bg-gray-900 dark:border-gray-700">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center gap-3 dark:border-gray-700">
          <Server className="w-5 h-5 text-primary-600" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">System Information</h3>
        </div>
        <div className="p-6">
          <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">API Version</dt>
              <dd className="text-sm text-gray-900 dark:text-white mt-1">2.0.0</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Frontend Version</dt>
              <dd className="text-sm text-gray-900 dark:text-white mt-1">2.0.0</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Database</dt>
              <dd className="text-sm text-gray-900 dark:text-white mt-1">PostgreSQL 16 + Redis 7</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Migration</dt>
              <dd className="text-sm text-gray-900 dark:text-white mt-1">Alembic (e1580e735101)</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  )
}
