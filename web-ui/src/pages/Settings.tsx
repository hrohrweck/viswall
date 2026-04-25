import { useState, useEffect } from 'react'
import { Settings as SettingsIcon, Save, RefreshCw, Bot, Server, Palette } from 'lucide-react'
import { useLLMConfig, useUpdateLLMConfig } from '../hooks/useApi'
import { useAuthStore } from '../stores/auth'
import { LoadingSpinner, EmptyState } from '../components/ui'
import type { LLMConfig } from '../types'

type Theme = 'light' | 'dark' | 'system'

export function Settings() {
  const { user } = useAuthStore()
  const isAdmin = user?.role === 'admin' || user?.role === 'superadmin'

  const { data: llmConfig, isLoading: llmLoading } = useLLMConfig()
  const updateLLM = useUpdateLLMConfig()

  const [theme, setTheme] = useState<Theme>(() => {
    return (localStorage.getItem('viswall-theme') as Theme) || 'system'
  })

  const [form, setForm] = useState<LLMConfig | null>(null)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (llmConfig) {
      setForm(llmConfig)
    }
  }, [llmConfig])

  useEffect(() => {
    localStorage.setItem('viswall-theme', theme)
    // Apply theme class to document
    const root = document.documentElement
    if (theme === 'dark') {
      root.classList.add('dark')
    } else if (theme === 'light') {
      root.classList.remove('dark')
    } else {
      // system
      if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        root.classList.add('dark')
      } else {
        root.classList.remove('dark')
      }
    }
  }, [theme])

  const handleSaveLLM = async () => {
    if (!form) return
    await updateLLM.mutateAsync(form)
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  if (llmLoading) return <LoadingSpinner />

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
            {form ? (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className={labelClass}>Provider</label>
                    <select
                      value={form.provider}
                      onChange={(e) => setForm({ ...form, provider: e.target.value })}
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
                      value={form.model}
                      onChange={(e) => setForm({ ...form, model: e.target.value })}
                      className={inputClass}
                      placeholder="gpt-4"
                    />
                  </div>
                </div>

                <div>
                  <label className={labelClass}>API Key</label>
                  <input
                    type="password"
                    value={form.api_key || ''}
                    onChange={(e) => setForm({ ...form, api_key: e.target.value || undefined })}
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
                    value={form.api_base || ''}
                    onChange={(e) => setForm({ ...form, api_base: e.target.value || undefined })}
                    className={inputClass}
                    placeholder="https://api.openai.com/v1"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className={labelClass}>Temperature ({form.temperature})</label>
                    <input
                      type="range"
                      min={0}
                      max={2}
                      step={0.1}
                      value={form.temperature}
                      onChange={(e) =>
                        setForm({ ...form, temperature: parseFloat(e.target.value) })
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
                      value={form.max_tokens}
                      onChange={(e) =>
                        setForm({ ...form, max_tokens: parseInt(e.target.value) })
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
                    value={form.system_prompt}
                    onChange={(e) => setForm({ ...form, system_prompt: e.target.value })}
                    className={inputClass + ' min-h-[80px]'}
                    rows={3}
                  />
                </div>

                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="auto_classify"
                      checked={form.auto_classify}
                      onChange={(e) =>
                        setForm({ ...form, auto_classify: e.target.checked })
                      }
                      className="w-4 h-4"
                    />
                    <label htmlFor="auto_classify" className="text-sm text-gray-700 dark:text-gray-300">
                      Auto-classify emails
                    </label>
                  </div>
                </div>

                {form.auto_classify && (
                  <div>
                    <label className={labelClass}>
                      Confidence Threshold ({form.confidence_threshold})
                    </label>
                    <input
                      type="range"
                      min={0}
                      max={1}
                      step={0.05}
                      value={form.confidence_threshold}
                      onChange={(e) =>
                        setForm({
                          ...form,
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
