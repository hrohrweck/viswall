import { useState } from 'react'
import {
  Bot,
  Plus,
  Trash2,
  Pencil,
  TestTube,
  Save,
  X,
  Server,
  Cpu,
  Settings,
} from 'lucide-react'
import {
  useLLMProviders,
  useCreateLLMProvider,
  useUpdateLLMProvider,
  useDeleteLLMProvider,
  useTestLLMProvider,
  useLLMModels,
  useCreateLLMModel,
  useUpdateLLMModel,
  useDeleteLLMModel,
  useLLMUseCaseConfigs,
  useUpdateLLMUseCaseConfig,
} from '../../hooks/useApi'
import { LoadingSpinner, EmptyState } from '../../components/ui'
import type {
  LLMProvider,
  LLMProviderCreate,
  LLMModel,
  LLMModelCreate,
  LLMUseCaseConfig,
} from '../../types'

type Tab = 'providers' | 'models' | 'use-cases'

export function LLMConfiguration() {
  const [activeTab, setActiveTab] = useState<Tab>('providers')

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
        LLM Configuration
      </h2>

      <div className="border-b border-gray-200 dark:border-gray-700 mb-6">
        <nav className="flex gap-6">
          {[
            { id: 'providers' as Tab, label: 'Providers', icon: Server },
            { id: 'models' as Tab, label: 'Models', icon: Cpu },
            { id: 'use-cases' as Tab, label: 'Use Cases', icon: Settings },
          ].map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`flex items-center gap-2 pb-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === id
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </nav>
      </div>

      {activeTab === 'providers' && <ProvidersTab />}
      {activeTab === 'models' && <ModelsTab />}
      {activeTab === 'use-cases' && <UseCasesTab />}
    </div>
  )
}

// ============================================================================
// PROVIDERS TAB
// ============================================================================

function ProvidersTab() {
  const { data: providers, isLoading } = useLLMProviders()
  const createProvider = useCreateLLMProvider()
  const updateProvider = useUpdateLLMProvider()
  const deleteProvider = useDeleteLLMProvider()
  const testProvider = useTestLLMProvider()

  const [editing, setEditing] = useState<LLMProvider | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<LLMProviderCreate>({
    name: '',
    provider_type: 'ollama',
    base_url: '',
    api_key: '',
    is_enabled: true,
    is_default: false,
  })
  const [testResult, setTestResult] = useState<string | null>(null)

  const handleSubmit = async () => {
    if (editing) {
      await updateProvider.mutateAsync({ id: editing.id, ...form })
      setEditing(null)
    } else {
      await createProvider.mutateAsync(form)
    }
    setShowForm(false)
    setForm({ name: '', provider_type: 'ollama', base_url: '', api_key: '', is_enabled: true, is_default: false })
  }

  const handleTest = async (id: number) => {
    setTestResult(null)
    try {
      const result = await testProvider.mutateAsync(id)
      setTestResult(`Success: ${result.response}`)
    } catch (err: any) {
      setTestResult(`Failed: ${err?.response?.data?.detail || 'Connection error'}`)
    }
  }

  if (isLoading) return <LoadingSpinner />

  const inputClass =
    'w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white dark:bg-gray-800 dark:border-gray-700 dark:text-white'
  const labelClass = 'block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1'

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">LLM Providers</h3>
        <button
          onClick={() => { setShowForm(true); setEditing(null); }}
          className="flex items-center gap-2 px-3 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700"
        >
          <Plus className="w-4 h-4" />
          Add Provider
        </button>
      </div>

      {testResult && (
        <div className={`p-3 rounded-lg text-sm ${testResult.startsWith('Success') ? 'bg-green-50 text-green-700 dark:bg-green-900/20' : 'bg-red-50 text-red-700 dark:bg-red-900/20'}`}>
          {testResult}
        </div>
      )}

      {showForm && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 dark:bg-gray-900 dark:border-gray-700">
          <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">
            {editing ? 'Edit Provider' : 'New Provider'}
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Name</label>
              <input className={inputClass} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Local Ollama" />
            </div>
            <div>
              <label className={labelClass}>Type</label>
              <select className={inputClass} value={form.provider_type} onChange={(e) => setForm({ ...form, provider_type: e.target.value as any })}>
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
                <option value="ollama">Ollama</option>
                <option value="custom">Custom</option>
              </select>
            </div>
            <div>
              <label className={labelClass}>Base URL (optional)</label>
              <input className={inputClass} value={form.base_url || ''} onChange={(e) => setForm({ ...form, base_url: e.target.value })} placeholder="http://ollama:11434" />
            </div>
            <div>
              <label className={labelClass}>API Key (optional)</label>
              <input type="password" className={inputClass} value={form.api_key || ''} onChange={(e) => setForm({ ...form, api_key: e.target.value })} placeholder="sk-..." />
            </div>
          </div>
          <div className="flex items-center gap-4 mt-4">
            <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
              <input type="checkbox" checked={form.is_enabled} onChange={(e) => setForm({ ...form, is_enabled: e.target.checked })} />
              Enabled
            </label>
            <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
              <input type="checkbox" checked={form.is_default} onChange={(e) => setForm({ ...form, is_default: e.target.checked })} />
              Default
            </label>
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <button onClick={() => setShowForm(false)} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
            <button onClick={handleSubmit} disabled={!form.name} className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700 disabled:opacity-50">
              <Save className="w-4 h-4 inline mr-1" />
              Save
            </button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 dark:bg-gray-900 dark:border-gray-700 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-gray-700 dark:text-gray-300">Name</th>
              <th className="px-4 py-3 text-left font-medium text-gray-700 dark:text-gray-300">Type</th>
              <th className="px-4 py-3 text-left font-medium text-gray-700 dark:text-gray-300">Base URL</th>
              <th className="px-4 py-3 text-left font-medium text-gray-700 dark:text-gray-300">Status</th>
              <th className="px-4 py-3 text-right font-medium text-gray-700 dark:text-gray-300">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {providers?.map((p) => (
              <tr key={p.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                <td className="px-4 py-3 text-gray-900 dark:text-white">{p.name}</td>
                <td className="px-4 py-3 text-gray-600 dark:text-gray-400 capitalize">{p.provider_type}</td>
                <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{p.base_url || '-'}</td>
                <td className="px-4 py-3">
                  <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${p.is_enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                    {p.is_enabled ? 'Enabled' : 'Disabled'}
                  </span>
                  {p.is_default && (
                    <span className="ml-2 inline-flex px-2 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-700">Default</span>
                  )}
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex justify-end gap-2">
                    <button onClick={() => handleTest(p.id)} className="p-1 text-gray-500 hover:text-primary-600" title="Test connection">
                      <TestTube className="w-4 h-4" />
                    </button>
                    <button onClick={() => { setEditing(p); setForm(p); setShowForm(true); }} className="p-1 text-gray-500 hover:text-blue-600" title="Edit">
                      <Pencil className="w-4 h-4" />
                    </button>
                    <button onClick={() => { if (confirm('Delete this provider?')) deleteProvider.mutate(p.id); }} className="p-1 text-gray-500 hover:text-red-600" title="Delete">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {(!providers || providers.length === 0) && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
                  <EmptyState icon={Server} title="No providers" description="Add an LLM provider to get started." />
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ============================================================================
// MODELS TAB
// ============================================================================

function ModelsTab() {
  const { data: providers } = useLLMProviders()
  const { data: models, isLoading } = useLLMModels()
  const createModel = useCreateLLMModel()
  const updateModel = useUpdateLLMModel()
  const deleteModel = useDeleteLLMModel()

  const [editing, setEditing] = useState<LLMModel | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<LLMModelCreate>({
    provider_id: 0,
    name: '',
    display_name: '',
    description: '',
    max_tokens: 4096,
    supports_vision: false,
    is_enabled: true,
  })

  const handleSubmit = async () => {
    if (editing) {
      await updateModel.mutateAsync({ id: editing.id, ...form })
      setEditing(null)
    } else {
      await createModel.mutateAsync(form)
    }
    setShowForm(false)
    setForm({ provider_id: 0, name: '', display_name: '', description: '', max_tokens: 4096, supports_vision: false, is_enabled: true })
  }

  if (isLoading) return <LoadingSpinner />

  const inputClass =
    'w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white dark:bg-gray-800 dark:border-gray-700 dark:text-white'
  const labelClass = 'block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1'

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">LLM Models</h3>
        <button
          onClick={() => { setShowForm(true); setEditing(null); }}
          className="flex items-center gap-2 px-3 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700"
        >
          <Plus className="w-4 h-4" />
          Add Model
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 dark:bg-gray-900 dark:border-gray-700">
          <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">
            {editing ? 'Edit Model' : 'New Model'}
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Provider</label>
              <select className={inputClass} value={form.provider_id} onChange={(e) => setForm({ ...form, provider_id: parseInt(e.target.value) })}>
                <option value={0}>Select provider...</option>
                {providers?.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className={labelClass}>Model ID</label>
              <input className={inputClass} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="qwen3.5:9b" />
            </div>
            <div>
              <label className={labelClass}>Display Name</label>
              <input className={inputClass} value={form.display_name || ''} onChange={(e) => setForm({ ...form, display_name: e.target.value })} placeholder="Qwen 3.5 9B" />
            </div>
            <div>
              <label className={labelClass}>Max Tokens</label>
              <input type="number" className={inputClass} value={form.max_tokens ?? ''} onChange={(e) => setForm({ ...form, max_tokens: parseInt(e.target.value) })} />
            </div>
            <div className="md:col-span-2">
              <label className={labelClass}>Description</label>
              <input className={inputClass} value={form.description || ''} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Optional description" />
            </div>
          </div>
          <div className="flex items-center gap-4 mt-4">
            <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
              <input type="checkbox" checked={form.is_enabled} onChange={(e) => setForm({ ...form, is_enabled: e.target.checked })} />
              Enabled
            </label>
            <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
              <input type="checkbox" checked={form.supports_vision} onChange={(e) => setForm({ ...form, supports_vision: e.target.checked })} />
              Supports Vision
            </label>
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <button onClick={() => setShowForm(false)} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
            <button onClick={handleSubmit} disabled={!form.name || form.provider_id === 0} className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700 disabled:opacity-50">
              <Save className="w-4 h-4 inline mr-1" />
              Save
            </button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 dark:bg-gray-900 dark:border-gray-700 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-gray-700 dark:text-gray-300">Name</th>
              <th className="px-4 py-3 text-left font-medium text-gray-700 dark:text-gray-300">Provider</th>
              <th className="px-4 py-3 text-left font-medium text-gray-700 dark:text-gray-300">Max Tokens</th>
              <th className="px-4 py-3 text-left font-medium text-gray-700 dark:text-gray-300">Status</th>
              <th className="px-4 py-3 text-right font-medium text-gray-700 dark:text-gray-300">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {models?.map((m) => (
              <tr key={m.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                <td className="px-4 py-3">
                  <div className="text-gray-900 dark:text-white">{m.display_name || m.name}</div>
                  <div className="text-xs text-gray-500">{m.name}</div>
                </td>
                <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                  {providers?.find((p) => p.id === m.provider_id)?.name || m.provider_id}
                </td>
                <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{m.max_tokens || '-'}</td>
                <td className="px-4 py-3">
                  <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${m.is_enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                    {m.is_enabled ? 'Enabled' : 'Disabled'}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex justify-end gap-2">
                    <button onClick={() => { setEditing(m); setForm(m); setShowForm(true); }} className="p-1 text-gray-500 hover:text-blue-600">
                      <Pencil className="w-4 h-4" />
                    </button>
                    <button onClick={() => { if (confirm('Delete this model?')) deleteModel.mutate(m.id); }} className="p-1 text-gray-500 hover:text-red-600">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {(!models || models.length === 0) && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
                  <EmptyState icon={Cpu} title="No models" description="Add an LLM model to get started." />
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ============================================================================
// USE CASES TAB
// ============================================================================

function UseCasesTab() {
  const { data: configs, isLoading } = useLLMUseCaseConfigs()
  const { data: providers } = useLLMProviders()
  const { data: models } = useLLMModels()
  const updateConfig = useUpdateLLMUseCaseConfig()

  const [editing, setEditing] = useState<LLMUseCaseConfig | null>(null)
  const [form, setForm] = useState<Partial<LLMUseCaseConfig>>({})

  const handleEdit = (config: LLMUseCaseConfig) => {
    setEditing(config)
    setForm(config)
  }

  const handleSave = async () => {
    if (!editing) return
    await updateConfig.mutateAsync({ id: editing.id, ...form })
    setEditing(null)
    setForm({})
  }

  if (isLoading) return <LoadingSpinner />

  const inputClass =
    'w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white dark:bg-gray-800 dark:border-gray-700 dark:text-white'
  const labelClass = 'block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1'

  const useCaseLabels: Record<string, string> = {
    email_classification: 'Email Classification',
    assistant_chat: 'Assistant Chat',
    security_audit: 'Security Audit',
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Use Case Configurations</h3>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {configs?.map((config) => (
          <div key={config.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 dark:bg-gray-900 dark:border-gray-700">
            {editing?.id === config.id ? (
              <div className="space-y-4">
                <div>
                  <label className={labelClass}>Provider</label>
                  <select className={inputClass} value={form.provider_id || ''} onChange={(e) => setForm({ ...form, provider_id: e.target.value ? parseInt(e.target.value) : null })}>
                    <option value="">Auto-select</option>
                    {providers?.map((p) => (
                      <option key={p.id} value={p.id}>{p.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className={labelClass}>Model</label>
                  <select className={inputClass} value={form.model_id || ''} onChange={(e) => setForm({ ...form, model_id: e.target.value ? parseInt(e.target.value) : null })}>
                    <option value="">Auto-select</option>
                    {models?.filter((m) => !form.provider_id || m.provider_id === form.provider_id).map((m) => (
                      <option key={m.id} value={m.id}>{m.display_name || m.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className={labelClass}>Temperature ({form.temperature})</label>
                  <input type="range" min={0} max={2} step={0.1} className="w-full" value={form.temperature || 0.3} onChange={(e) => setForm({ ...form, temperature: parseFloat(e.target.value) })} />
                </div>
                <div>
                  <label className={labelClass}>Max Tokens</label>
                  <input type="number" className={inputClass} value={form.max_tokens || 500} onChange={(e) => setForm({ ...form, max_tokens: parseInt(e.target.value) })} />
                </div>
                <div>
                  <label className={labelClass}>System Prompt</label>
                  <textarea className={inputClass + ' min-h-[80px]'} rows={3} value={form.system_prompt || ''} onChange={(e) => setForm({ ...form, system_prompt: e.target.value })} />
                </div>
                <div className="flex justify-end gap-2">
                  <button onClick={() => { setEditing(null); setForm({}); }} className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800">
                    <X className="w-4 h-4 inline mr-1" />
                    Cancel
                  </button>
                  <button onClick={handleSave} className="px-3 py-1.5 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700">
                    <Save className="w-4 h-4 inline mr-1" />
                    Save
                  </button>
                </div>
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-sm font-semibold text-gray-900 dark:text-white">{useCaseLabels[config.use_case] || config.use_case}</h4>
                  <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${config.is_enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                    {config.is_enabled ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
                <dl className="space-y-2 text-sm">
                  <div>
                    <dt className="text-gray-500 dark:text-gray-400">Provider</dt>
                    <dd className="text-gray-900 dark:text-white">{providers?.find((p) => p.id === config.provider_id)?.name || 'Not set'}</dd>
                  </div>
                  <div>
                    <dt className="text-gray-500 dark:text-gray-400">Model</dt>
                    <dd className="text-gray-900 dark:text-white">{models?.find((m) => m.id === config.model_id)?.display_name || models?.find((m) => m.id === config.model_id)?.name || 'Not set'}</dd>
                  </div>
                  <div>
                    <dt className="text-gray-500 dark:text-gray-400">Temperature</dt>
                    <dd className="text-gray-900 dark:text-white">{config.temperature}</dd>
                  </div>
                  <div>
                    <dt className="text-gray-500 dark:text-gray-400">Max Tokens</dt>
                    <dd className="text-gray-900 dark:text-white">{config.max_tokens}</dd>
                  </div>
                  <div>
                    <dt className="text-gray-500 dark:text-gray-400">System Prompt</dt>
                    <dd className="text-gray-900 dark:text-white truncate">{config.system_prompt || '-'}</dd>
                  </div>
                </dl>
                <button onClick={() => handleEdit(config)} className="mt-4 flex items-center gap-2 px-3 py-2 text-sm text-primary-600 hover:text-primary-700">
                  <Pencil className="w-4 h-4" />
                  Edit Configuration
                </button>
              </>
            )}
          </div>
        ))}
        {(!configs || configs.length === 0) && (
          <div className="lg:col-span-3">
            <EmptyState icon={Settings} title="No use cases configured" description="Use cases are seeded automatically on first migration." />
          </div>
        )}
      </div>
    </div>
  )
}
