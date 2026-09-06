import { useState } from 'react'
import {
  Bot,
  Plus,
  Pencil,
  TestTube,
  Trash2,
  Save,
  X,
  Server,
  Cpu,
  Settings,
  CheckCircle2,
  XCircle,
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
import {
  PageHeader,
  Tabs,
  TabsContent,
  DataTable,
  Modal,
  ConfirmDialog,
  Badge,
  Button,
  IconButton,
  Field,
  Input,
  Select,
  Card,
  CardBody,
  EmptyState,
} from '../../components/ui'
import { toast } from '../../components/ui/Toaster'
import { getErrMsg } from '../../lib/utils'
import type { Column } from '../../components/ui/DataTable'
import type {
  LLMProvider,
  LLMProviderCreate,
  LLMModel,
  LLMModelCreate,
  LLMUseCaseConfig,
} from '../../types'

/* -------------------------------------------------------------------------- */
/*  Provider type → Badge variant mapping                                     */
/* -------------------------------------------------------------------------- */

const providerTypeVariant: Record<
  LLMProvider['provider_type'],
  'success' | 'info' | 'warning' | 'neutral'
> = {
  openai: 'success',
  anthropic: 'info',
  ollama: 'warning',
  custom: 'neutral',
}

/* -------------------------------------------------------------------------- */
/*  Main page                                                                  */
/* -------------------------------------------------------------------------- */

export function LLMConfiguration() {
  const [activeTab, setActiveTab] = useState('providers')

  return (
    <div className="space-y-6">
      <PageHeader
        title="LLM Providers"
        description="Manage AI providers, models, and use-case configurations for email classification and assistant features."
      />

      <Tabs
        items={[
          { value: 'providers', label: 'Providers' },
          { value: 'models', label: 'Models' },
          { value: 'use-cases', label: 'Use Cases' },
        ]}
        value={activeTab}
        onValueChange={setActiveTab}
      >
        <TabsContent value="providers">
          <ProvidersTab />
        </TabsContent>
        <TabsContent value="models">
          <ModelsTab />
        </TabsContent>
        <TabsContent value="use-cases">
          <UseCasesTab />
        </TabsContent>
      </Tabs>
    </div>
  )
}

/* ====================================================================== */
/*  PROVIDERS TAB                                                          */
/* ====================================================================== */

const EMPTY_PROVIDER_FORM: LLMProviderCreate = {
  name: '',
  provider_type: 'ollama',
  base_url: '',
  api_key: '',
  is_enabled: true,
  is_default: false,
}

function ProvidersTab() {
  const { data: providers, isLoading } = useLLMProviders()
  const createProvider = useCreateLLMProvider()
  const updateProvider = useUpdateLLMProvider()
  const deleteProvider = useDeleteLLMProvider()
  const testProvider = useTestLLMProvider()

  const [editing, setEditing] = useState<LLMProvider | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<LLMProviderCreate>(EMPTY_PROVIDER_FORM)

  /* Per-provider test result state */
  const [testingId, setTestingId] = useState<number | null>(null)
  const [testResult, setTestResult] = useState<{
    id: number
    success: boolean
    message: string
  } | null>(null)

  /* Delete confirmation state */
  const [deleteTarget, setDeleteTarget] = useState<LLMProvider | null>(null)

  const handleOpenCreate = () => {
    setEditing(null)
    setForm(EMPTY_PROVIDER_FORM)
    setShowForm(true)
  }

  const handleOpenEdit = (p: LLMProvider) => {
    setEditing(p)
    setForm({
      name: p.name,
      provider_type: p.provider_type,
      base_url: p.base_url ?? '',
      api_key: p.api_key ?? '',
      is_enabled: p.is_enabled,
      is_default: p.is_default,
    })
    setShowForm(true)
  }

  const handleSubmit = async () => {
    try {
      if (editing) {
        await updateProvider.mutateAsync({ id: editing.id, ...form })
        toast.success('Provider updated')
      } else {
        await createProvider.mutateAsync(form)
        toast.success('Provider created')
      }
      setShowForm(false)
      setEditing(null)
      setForm(EMPTY_PROVIDER_FORM)
    } catch (e) {
      toast.error(getErrMsg(e))
    }
  }

  const handleTest = async (id: number) => {
    setTestingId(id)
    setTestResult(null)
    try {
      const result = await testProvider.mutateAsync(id)
      setTestResult({ id, success: true, message: result.response })
    } catch (e) {
      setTestResult({ id, success: false, message: getErrMsg(e) })
    } finally {
      setTestingId(null)
    }
  }

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return
    try {
      await deleteProvider.mutateAsync(deleteTarget.id)
      toast.success('Provider deleted')
    } catch (e) {
      toast.error(getErrMsg(e))
    } finally {
      setDeleteTarget(null)
    }
  }

  const columns: Column<LLMProvider>[] = [
    {
      key: 'name',
      header: 'Name',
      render: (p) => (
        <span className="font-medium text-on-surface">{p.name}</span>
      ),
    },
    {
      key: 'provider_type',
      header: 'Type',
      render: (p) => (
        <Badge variant={providerTypeVariant[p.provider_type] ?? 'neutral'}>
          {p.provider_type}
        </Badge>
      ),
    },
    {
      key: 'base_url',
      header: 'Base URL',
      render: (p) => (
        <span className="font-mono text-xs text-on-surface-muted">
          {p.base_url || '—'}
        </span>
      ),
    },
    {
      key: 'is_enabled',
      header: 'Status',
      render: (p) => (
        <div className="flex items-center gap-2">
          <Badge variant={p.is_enabled ? 'success' : 'neutral'}>
            {p.is_enabled ? 'Enabled' : 'Disabled'}
          </Badge>
          {p.is_default && <Badge variant="info">Default</Badge>}
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={handleOpenCreate} icon={Plus}>
          Add provider
        </Button>
      </div>

      <DataTable
        columns={columns}
        data={providers ?? []}
        keyExtractor={(p) => p.id}
        searchable
        searchPlaceholder="Search providers…"
        isLoading={isLoading}
        emptyContent={
          <EmptyState
            icon={Server}
            title="No providers"
            description="Add an LLM provider to get started."
          />
        }
        rowActions={(p) => (
          <div className="flex items-center justify-end gap-1">
            <IconButton
              icon={TestTube}
              label="Test connection"
              size="sm"
              variant="ghost"
              onClick={(e) => {
                e.stopPropagation()
                handleTest(p.id)
              }}
              disabled={testingId === p.id}
            />
            <IconButton
              icon={Pencil}
              label="Edit"
              size="sm"
              variant="ghost"
              onClick={(e) => {
                e.stopPropagation()
                handleOpenEdit(p)
              }}
            />
            <IconButton
              icon={Trash2}
              label="Delete"
              size="sm"
              variant="ghost"
              className="text-danger hover:text-danger"
              onClick={(e) => {
                e.stopPropagation()
                setDeleteTarget(p)
              }}
            />
          </div>
        )}
      />

      {/* Per-provider test result */}
      {testResult && (
        <div
          className={`flex items-start gap-3 p-4 rounded-card border ${
            testResult.success
              ? 'border-success bg-success-subtle'
              : 'border-danger bg-danger-subtle'
          }`}
          role="alert"
        >
          {testResult.success ? (
            <CheckCircle2 className="h-5 w-5 text-success shrink-0 mt-0.5" />
          ) : (
            <XCircle className="h-5 w-5 text-danger shrink-0 mt-0.5" />
          )}
          <div className="min-w-0">
            <p className={`text-sm font-medium ${testResult.success ? 'text-success' : 'text-danger'}`}>
              {testResult.success ? 'Connection successful' : 'Connection failed'}
            </p>
            <p className="text-sm text-on-surface-muted mt-0.5 break-all">
              {testResult.message}
            </p>
          </div>
          <button
            onClick={() => setTestResult(null)}
            className="ml-auto shrink-0 text-on-surface-muted hover:text-on-surface"
            aria-label="Dismiss"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Add / Edit modal */}
      <Modal
        open={showForm}
        onClose={() => {
          setShowForm(false)
          setEditing(null)
        }}
        title={editing ? 'Edit Provider' : 'New Provider'}
        size="lg"
      >
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Name" required>
              <Input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Local Ollama"
              />
            </Field>
            <Field label="Type">
              <Select
                value={form.provider_type}
                onChange={(e) =>
                  setForm({
                    ...form,
                    provider_type: e.target.value as LLMProviderCreate['provider_type'],
                  })
                }
              >
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
                <option value="ollama">Ollama</option>
                <option value="custom">Custom</option>
              </Select>
            </Field>
            <Field label="Base URL" helper="Optional — required for Ollama and custom providers">
              <Input
                value={form.base_url ?? ''}
                onChange={(e) => setForm({ ...form, base_url: e.target.value })}
                placeholder="http://ollama:11434"
              />
            </Field>
            <Field label="API Key" helper="Optional — required for OpenAI and Anthropic">
              <Input
                type="password"
                value={form.api_key ?? ''}
                onChange={(e) => setForm({ ...form, api_key: e.target.value })}
                placeholder="sk-..."
              />
            </Field>
          </div>

          <div className="flex items-center gap-6">
            <label className="flex items-center gap-2 text-sm text-on-surface">
              <input
                type="checkbox"
                className="accent-primary"
                checked={form.is_enabled}
                onChange={(e) => setForm({ ...form, is_enabled: e.target.checked })}
              />
              Enabled
            </label>
            <label className="flex items-center gap-2 text-sm text-on-surface">
              <input
                type="checkbox"
                className="accent-primary"
                checked={form.is_default}
                onChange={(e) => setForm({ ...form, is_default: e.target.checked })}
              />
              Default
            </label>
          </div>

          <div className="flex justify-end gap-3 pt-2 border-t border-border">
            <Button
              variant="ghost"
              onClick={() => {
                setShowForm(false)
                setEditing(null)
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={!form.name}
              loading={createProvider.isPending || updateProvider.isPending}
              icon={Save}
            >
              Save
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete confirmation */}
      <ConfirmDialog
        open={deleteTarget !== null}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleConfirmDelete}
        title="Delete provider"
        message={`Are you sure you want to delete "${deleteTarget?.name}"?`}
        impact="All associated models will also be removed."
        confirmLabel="Delete"
        loading={deleteProvider.isPending}
      />
    </div>
  )
}

/* ====================================================================== */
/*  MODELS TAB                                                             */
/* ====================================================================== */

const EMPTY_MODEL_FORM: LLMModelCreate = {
  provider_id: 0,
  name: '',
  display_name: '',
  description: '',
  max_tokens: 4096,
  supports_vision: false,
  is_enabled: true,
}

function ModelsTab() {
  const { data: providers } = useLLMProviders()
  const { data: models, isLoading } = useLLMModels()
  const createModel = useCreateLLMModel()
  const updateModel = useUpdateLLMModel()
  const deleteModel = useDeleteLLMModel()

  const [editing, setEditing] = useState<LLMModel | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<LLMModelCreate>(EMPTY_MODEL_FORM)
  const [deleteTarget, setDeleteTarget] = useState<LLMModel | null>(null)

  const providerName = (id: number) =>
    providers?.find((p) => p.id === id)?.name ?? String(id)

  const handleOpenCreate = () => {
    setEditing(null)
    setForm(EMPTY_MODEL_FORM)
    setShowForm(true)
  }

  const handleOpenEdit = (m: LLMModel) => {
    setEditing(m)
    setForm({
      provider_id: m.provider_id,
      name: m.name,
      display_name: m.display_name ?? '',
      description: m.description ?? '',
      max_tokens: m.max_tokens ?? 4096,
      supports_vision: m.supports_vision,
      is_enabled: m.is_enabled,
    })
    setShowForm(true)
  }

  const handleSubmit = async () => {
    try {
      if (editing) {
        await updateModel.mutateAsync({ id: editing.id, ...form })
        toast.success('Model updated')
      } else {
        await createModel.mutateAsync(form)
        toast.success('Model created')
      }
      setShowForm(false)
      setEditing(null)
      setForm(EMPTY_MODEL_FORM)
    } catch (e) {
      toast.error(getErrMsg(e))
    }
  }

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return
    try {
      await deleteModel.mutateAsync(deleteTarget.id)
      toast.success('Model deleted')
    } catch (e) {
      toast.error(getErrMsg(e))
    } finally {
      setDeleteTarget(null)
    }
  }

  const columns: Column<LLMModel>[] = [
    {
      key: 'provider_id',
      header: 'Provider',
      render: (m) => providerName(m.provider_id),
    },
    {
      key: 'name',
      header: 'Model ID',
      render: (m) => (
        <div>
          <span className="font-mono text-xs">{m.name}</span>
          {m.display_name && (
            <p className="text-xs text-on-surface-muted">{m.display_name}</p>
          )}
        </div>
      ),
    },
    {
      key: 'description',
      header: 'Use case',
      render: (m) => (
        <span className="text-on-surface-muted">{m.description || '—'}</span>
      ),
    },
    {
      key: 'is_enabled',
      header: 'Status',
      render: (m) => (
        <Badge variant={m.is_enabled ? 'success' : 'neutral'}>
          {m.is_enabled ? 'Enabled' : 'Disabled'}
        </Badge>
      ),
    },
  ]

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={handleOpenCreate} icon={Plus}>
          Add model
        </Button>
      </div>

      <DataTable
        columns={columns}
        data={models ?? []}
        keyExtractor={(m) => m.id}
        searchable
        searchPlaceholder="Search models…"
        isLoading={isLoading}
        emptyContent={
          <EmptyState
            icon={Cpu}
            title="No models"
            description="Add an LLM model to get started."
          />
        }
        rowActions={(m) => (
          <div className="flex items-center justify-end gap-1">
            <IconButton
              icon={Pencil}
              label="Edit"
              size="sm"
              variant="ghost"
              onClick={(e) => {
                e.stopPropagation()
                handleOpenEdit(m)
              }}
            />
            <IconButton
              icon={Trash2}
              label="Delete"
              size="sm"
              variant="ghost"
              className="text-danger hover:text-danger"
              onClick={(e) => {
                e.stopPropagation()
                setDeleteTarget(m)
              }}
            />
          </div>
        )}
      />

      {/* Add / Edit modal */}
      <Modal
        open={showForm}
        onClose={() => {
          setShowForm(false)
          setEditing(null)
        }}
        title={editing ? 'Edit Model' : 'New Model'}
        size="lg"
      >
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Provider" required>
              <Select
                value={form.provider_id}
                onChange={(e) =>
                  setForm({ ...form, provider_id: parseInt(e.target.value) })
                }
              >
                <option value={0}>Select provider…</option>
                {providers?.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Model ID" required>
              <Input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="qwen3.5:9b"
                mono
              />
            </Field>
            <Field label="Display Name">
              <Input
                value={form.display_name ?? ''}
                onChange={(e) =>
                  setForm({ ...form, display_name: e.target.value })
                }
                placeholder="Qwen 3.5 9B"
              />
            </Field>
            <Field label="Max Tokens">
              <Input
                type="number"
                value={form.max_tokens ?? ''}
                onChange={(e) =>
                  setForm({ ...form, max_tokens: parseInt(e.target.value) })
                }
              />
            </Field>
            <div className="md:col-span-2">
              <Field label="Description">
                <Input
                  value={form.description ?? ''}
                  onChange={(e) =>
                    setForm({ ...form, description: e.target.value })
                  }
                  placeholder="Optional description"
                />
              </Field>
            </div>
          </div>

          <div className="flex items-center gap-6">
            <label className="flex items-center gap-2 text-sm text-on-surface">
              <input
                type="checkbox"
                className="accent-primary"
                checked={form.is_enabled}
                onChange={(e) =>
                  setForm({ ...form, is_enabled: e.target.checked })
                }
              />
              Enabled
            </label>
            <label className="flex items-center gap-2 text-sm text-on-surface">
              <input
                type="checkbox"
                className="accent-primary"
                checked={form.supports_vision}
                onChange={(e) =>
                  setForm({ ...form, supports_vision: e.target.checked })
                }
              />
              Supports Vision
            </label>
          </div>

          <div className="flex justify-end gap-3 pt-2 border-t border-border">
            <Button
              variant="ghost"
              onClick={() => {
                setShowForm(false)
                setEditing(null)
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={!form.name || form.provider_id === 0}
              loading={createModel.isPending || updateModel.isPending}
              icon={Save}
            >
              Save
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete confirmation */}
      <ConfirmDialog
        open={deleteTarget !== null}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleConfirmDelete}
        title="Delete model"
        message={`Are you sure you want to delete "${deleteTarget?.display_name || deleteTarget?.name}"?`}
        confirmLabel="Delete"
        loading={deleteModel.isPending}
      />
    </div>
  )
}

/* ====================================================================== */
/*  USE CASES TAB                                                          */
/* ====================================================================== */

const useCaseLabels: Record<string, string> = {
  email_classification: 'Email Classification',
  assistant_chat: 'Assistant Chat',
  security_audit: 'Security Audit',
}

function UseCasesTab() {
  const { data: configs, isLoading } = useLLMUseCaseConfigs()
  const { data: providers } = useLLMProviders()
  const { data: models } = useLLMModels()
  const updateConfig = useUpdateLLMUseCaseConfig()

  const [editingId, setEditingId] = useState<number | null>(null)
  const [form, setForm] = useState<Partial<LLMUseCaseConfig>>({})

  const handleEdit = (config: LLMUseCaseConfig) => {
    setEditingId(config.id)
    setForm({ ...config })
  }

  const handleSave = async () => {
    if (editingId == null) return
    try {
      await updateConfig.mutateAsync({ id: editingId, ...form })
      toast.success('Use case configuration saved')
      setEditingId(null)
      setForm({})
    } catch (e) {
      toast.error(getErrMsg(e))
    }
  }

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={i}>
            <CardBody>
              <div className="space-y-3 animate-pulse">
                <div className="h-4 bg-surface-elevated rounded w-1/2" />
                <div className="h-3 bg-surface-elevated rounded w-3/4" />
                <div className="h-3 bg-surface-elevated rounded w-2/3" />
              </div>
            </CardBody>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {configs?.map((config) => (
          <Card key={config.id}>
            <CardBody>
              {editingId === config.id ? (
                <div className="space-y-4">
                  <Field label="Provider">
                    <Select
                      value={form.provider_id ?? ''}
                      onChange={(e) =>
                        setForm({
                          ...form,
                          provider_id: e.target.value
                            ? parseInt(e.target.value)
                            : null,
                        })
                      }
                    >
                      <option value="">Auto-select</option>
                      {providers?.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name}
                        </option>
                      ))}
                    </Select>
                  </Field>
                  <Field label="Model">
                    <Select
                      value={form.model_id ?? ''}
                      onChange={(e) =>
                        setForm({
                          ...form,
                          model_id: e.target.value
                            ? parseInt(e.target.value)
                            : null,
                        })
                      }
                    >
                      <option value="">Auto-select</option>
                      {models
                        ?.filter(
                          (m) =>
                            !form.provider_id ||
                            m.provider_id === form.provider_id,
                        )
                        .map((m) => (
                          <option key={m.id} value={m.id}>
                            {m.display_name || m.name}
                          </option>
                        ))}
                    </Select>
                  </Field>
                  <Field
                    label={`Temperature (${form.temperature ?? 0.3})`}
                  >
                    <input
                      type="range"
                      min={0}
                      max={2}
                      step={0.1}
                      className="w-full accent-primary"
                      value={form.temperature ?? 0.3}
                      onChange={(e) =>
                        setForm({
                          ...form,
                          temperature: parseFloat(e.target.value),
                        })
                      }
                    />
                  </Field>
                  <Field label="Max Tokens">
                    <Input
                      type="number"
                      value={form.max_tokens ?? 500}
                      onChange={(e) =>
                        setForm({
                          ...form,
                          max_tokens: parseInt(e.target.value),
                        })
                      }
                    />
                  </Field>
                  <Field label="System Prompt">
                    <textarea
                      className="min-h-[5rem] w-full rounded-card border border-border bg-surface-card px-3 py-2 text-sm text-on-surface placeholder:text-on-surface-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                      rows={3}
                      value={form.system_prompt ?? ''}
                      onChange={(e) =>
                        setForm({ ...form, system_prompt: e.target.value })
                      }
                    />
                  </Field>
                  <div className="flex justify-end gap-2 pt-2 border-t border-border">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setEditingId(null)
                        setForm({})
                      }}
                      icon={X}
                    >
                      Cancel
                    </Button>
                    <Button
                      size="sm"
                      onClick={handleSave}
                      loading={updateConfig.isPending}
                      icon={Save}
                    >
                      Save
                    </Button>
                  </div>
                </div>
              ) : (
                <>
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="text-sm font-semibold text-on-surface">
                      {useCaseLabels[config.use_case] || config.use_case}
                    </h4>
                    <Badge
                      variant={config.is_enabled ? 'success' : 'neutral'}
                    >
                      {config.is_enabled ? 'Enabled' : 'Disabled'}
                    </Badge>
                  </div>
                  <dl className="space-y-2 text-sm">
                    <div>
                      <dt className="text-on-surface-muted">Provider</dt>
                      <dd className="text-on-surface">
                        {providers?.find((p) => p.id === config.provider_id)
                          ?.name || 'Not set'}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-on-surface-muted">Model</dt>
                      <dd className="text-on-surface">
                        {models?.find((m) => m.id === config.model_id)
                          ?.display_name ||
                          models?.find((m) => m.id === config.model_id)
                            ?.name ||
                          'Not set'}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-on-surface-muted">Temperature</dt>
                      <dd className="text-on-surface">{config.temperature}</dd>
                    </div>
                    <div>
                      <dt className="text-on-surface-muted">Max Tokens</dt>
                      <dd className="text-on-surface">{config.max_tokens}</dd>
                    </div>
                    <div>
                      <dt className="text-on-surface-muted">System Prompt</dt>
                      <dd className="text-on-surface truncate">
                        {config.system_prompt || '—'}
                      </dd>
                    </div>
                  </dl>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="mt-4"
                    onClick={() => handleEdit(config)}
                    icon={Pencil}
                  >
                    Edit Configuration
                  </Button>
                </>
              )}
            </CardBody>
          </Card>
        ))}
        {(!configs || configs.length === 0) && (
          <div className="lg:col-span-3">
            <EmptyState
              icon={Settings}
              title="No use cases configured"
              description="Use cases are seeded automatically on first migration."
            />
          </div>
        )}
      </div>
    </div>
  )
}
