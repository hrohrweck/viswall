import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Check, Mail, Shield, Brain, Globe } from 'lucide-react'
import { useInstanceStore } from '../../stores/instance'
import { useCreateMailDomain, useLLMModels } from '../../hooks/useApi'
import {
  PageHeader,
  Card,
  Button,
  Field,
  Input,
  Select,
  Switch,
  toast,
  buttonVariants,
} from '../../components/ui'

const STEPS = ['Domain', 'Security', 'Review'] as const

const LLM_MODELS_STATIC = [
  { value: 'gpt-4', label: 'GPT-4' },
  { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
  { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
  { value: 'claude-3-opus', label: 'Claude 3 Opus' },
  { value: 'claude-3-sonnet', label: 'Claude 3 Sonnet' },
]

export function MailDomainCreate() {
  const navigate = useNavigate()
  const { selectedInstanceId } = useInstanceStore()
  const [step, setStep] = useState(0)
  const [config, setConfig] = useState({
    domain: '',
    enabled: true,
    spam_filter_enabled: true,
    virus_scan_enabled: true,
    dkim_enabled: true,
    dmarc_enabled: true,
    spf_enabled: true,
    llm_enabled: false,
    groupware_enabled: false,
    llm_config: {
      provider: 'openai',
      model: 'gpt-4',
      auto_classify: false,
      confidence_threshold: 0.8,
    },
  })

  const createMutation = useCreateMailDomain(selectedInstanceId!)
  const { data: llmModels } = useLLMModels()

  const modelOptions = llmModels && llmModels.length > 0
    ? llmModels.map((m) => ({ value: m.name, label: m.name }))
    : LLM_MODELS_STATIC

  const handleSubmit = async () => {
    if (!selectedInstanceId) return
    try {
      await createMutation.mutateAsync({
        domain: config.domain,
        enabled: config.enabled,
        spam_filter_enabled: config.spam_filter_enabled,
        virus_scan_enabled: config.virus_scan_enabled,
        dkim_enabled: config.dkim_enabled,
        dmarc_enabled: config.dmarc_enabled,
        spf_enabled: config.spf_enabled,
        llm_enabled: config.llm_enabled,
        llm_config: config.llm_config,
        groupware_enabled: config.groupware_enabled,
      })
      toast.success(`Domain "${config.domain}" created`)
      navigate('/mail')
    } catch {
      toast.error('Failed to create domain')
    }
  }

  const stepIndicator = (
    <div className="flex items-center gap-4 mb-8">
      {STEPS.map((label, i) => {
        const done = i < step
        const current = i === step
        return (
          <div key={label} className="flex items-center gap-2">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              done ? 'bg-primary text-white' : current ? 'ring-2 ring-primary text-primary bg-surface-card' : 'bg-surface-elevated text-on-surface-muted'
            }`}>
              {done ? <Check className="w-4 h-4" /> : i + 1}
            </div>
            <span className={`text-sm ${current ? 'text-on-surface font-medium' : 'text-on-surface-muted'}`}>{label}</span>
          </div>
        )
      })}
    </div>
  )

  const renderDomainStep = () => (
    <div className="space-y-6">
      <Field label="Domain Name" required helper="The domain you want to receive email for">
        <Input
          value={config.domain}
          onChange={(e) => setConfig({ ...config, domain: e.target.value })}
          placeholder="example.com"
          mono
        />
      </Field>
      <Card>
        <div className="flex items-start gap-3">
          <Mail className="w-5 h-5 text-info shrink-0 mt-0.5" />
          <div>
            <h4 className="font-medium text-on-surface">What happens next?</h4>
            <ul className="text-sm text-on-surface-muted mt-2 space-y-1">
              <li>• Mail server configured for {config.domain || 'your domain'}</li>
              <li>• DKIM keys generated for email signing</li>
              <li>• DNS records provided for SPF, DKIM, DMARC</li>
              <li>• You can start creating email users immediately</li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  )

  const renderSecurityStep = () => (
    <div className="space-y-6">
      <p className="text-sm text-on-surface-muted">Configure security features for this domain:</p>
      <div className="space-y-4">
        {([
          { key: 'spam_filter_enabled' as const, label: 'SpamAssassin Filter', desc: 'Bayesian filtering, Pyzor, Razor, and DCC network checks. Blocks 95%+ of spam.', icon: Shield, color: 'text-info' },
          { key: 'virus_scan_enabled' as const, label: 'ClamAV Virus Scanning', desc: 'Real-time virus and malware scanning with automatic signature updates.', icon: Shield, color: 'text-danger' },
          { key: 'dkim_enabled' as const, label: 'DKIM Signing', desc: 'Cryptographic email signing to prove authenticity. Required for good deliverability.', icon: Shield, color: 'text-success' },
          { key: 'dmarc_enabled' as const, label: 'DMARC Policy', desc: 'Domain-based Message Authentication. Protects against domain spoofing.', icon: Shield, color: 'text-info' },
          { key: 'llm_enabled' as const, label: 'AI Email Classification (LLM)', desc: 'Advanced email categorization using GPT-4 or Claude.', icon: Brain, color: 'text-info' },
          { key: 'groupware_enabled' as const, label: 'SOGo Groupware', desc: 'Enable CalDAV, CardDAV, and ActiveSync for this domain.', icon: Globe, color: 'text-warning' },
        ]).map(({ key, label, desc, icon: Icon, color }) => (
          <Card key={key}>
            <div className="flex items-start gap-4">
              <Switch
                checked={config[key]}
                onCheckedChange={(checked) => setConfig({ ...config, [key]: checked })}
                aria-label={label}
              />
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <Icon className={`w-4 h-4 ${color}`} />
                  <span className="font-medium text-on-surface">{label}</span>
                </div>
                <p className="text-sm text-on-surface-muted mt-1">{desc}</p>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {config.llm_enabled && (
        <div className="grid grid-cols-2 gap-4 mt-6">
          <Field label="LLM Provider">
            <Select
              value={config.llm_config.provider}
              onChange={(e) => setConfig({
                ...config,
                llm_config: { ...config.llm_config, provider: e.target.value },
              })}
            >
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic Claude</option>
              <option value="local">Local Model</option>
            </Select>
          </Field>
          <Field label="Model">
            <Select
              value={config.llm_config.model}
              onChange={(e) => setConfig({
                ...config,
                llm_config: { ...config.llm_config, model: e.target.value },
              })}
            >
              {modelOptions.map((m) => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </Select>
          </Field>
        </div>
      )}
    </div>
  )

  const renderReviewStep = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-on-surface">Review configuration</h3>
      <Card>
        <dl className="divide-y divide-border">
          {([
            { label: 'Domain', value: config.domain },
            { label: 'Status', value: config.enabled ? 'Active' : 'Disabled' },
            { label: 'Spam Filter', value: config.spam_filter_enabled ? 'Enabled' : 'Disabled' },
            { label: 'Virus Scan', value: config.virus_scan_enabled ? 'Enabled' : 'Disabled' },
            { label: 'DKIM Signing', value: config.dkim_enabled ? 'Enabled' : 'Disabled' },
            { label: 'DMARC Policy', value: config.dmarc_enabled ? 'Enabled' : 'Disabled' },
            { label: 'SPF', value: config.spf_enabled ? 'Enabled' : 'Disabled' },
            { label: 'LLM Classification', value: config.llm_enabled ? `Enabled (${config.llm_config.provider} / ${config.llm_config.model})` : 'Disabled' },
            { label: 'Groupware', value: config.groupware_enabled ? 'Enabled (SOGo)' : 'Disabled' },
          ]).map(({ label, value }) => (
            <div key={label} className="flex items-center justify-between py-3">
              <dt className="text-sm text-on-surface-muted">{label}</dt>
              <dd className="text-sm font-medium text-on-surface">{value}</dd>
            </div>
          ))}
        </dl>
      </Card>
    </div>
  )

  const canContinue = step === 0 ? config.domain.length > 0 : true

  return (
    <div>
      <Link to="/mail" className={buttonVariants({ variant: 'ghost', size: 'sm' }) + ' mb-4'}>
        ← Back to Mail
      </Link>

      <PageHeader title="Add Mail Domain" description="Configure a new email domain with security features" />

      <Card className="mt-6">
        {stepIndicator}

        {step === 0 && renderDomainStep()}
        {step === 1 && renderSecurityStep()}
        {step === 2 && renderReviewStep()}

        <div className="flex justify-between mt-8 pt-6 border-t border-border">
          <Button variant="secondary" onClick={() => step > 0 ? setStep(step - 1) : navigate('/mail')}>
            {step > 0 ? 'Back' : 'Cancel'}
          </Button>
          <div className="flex gap-3">
            {step < 2 ? (
              <Button onClick={() => setStep(step + 1)} disabled={!canContinue}>
                Continue
              </Button>
            ) : (
              <Button onClick={handleSubmit} disabled={createMutation.isPending}>
                {createMutation.isPending ? 'Creating...' : 'Create Domain'}
              </Button>
            )}
          </div>
        </div>
      </Card>
    </div>
  )
}
