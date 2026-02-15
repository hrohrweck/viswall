import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Shield, Brain, Mail, Check } from 'lucide-react'

export function MailDomainCreate() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [config, setConfig] = useState({
    domain: '',
    enabled: true,
    spam_filter_enabled: true,
    virus_scan_enabled: true,
    dkim_enabled: true,
    dmarc_enabled: true,
    spf_enabled: true,
    llm_enabled: false,
    llm_config: {
      provider: 'openai',
      model: 'gpt-4',
      auto_classify: false,
      confidence_threshold: 0.8,
    }
  })

  const handleSubmit = async () => {
    // API call would go here
    navigate('/mail')
  }

  const renderStep1 = () => (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Domain Name
        </label>
        <input
          type="text"
          value={config.domain}
          onChange={(e) => setConfig({ ...config, domain: e.target.value })}
          placeholder="example.com"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
        />
        <p className="text-sm text-gray-500 mt-1">
          The domain you want to receive email for
        </p>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Mail className="w-5 h-5 text-blue-600 mt-0.5" />
          <div>
            <h4 className="font-medium text-blue-900">What happens next?</h4>
            <ul className="text-sm text-blue-800 mt-2 space-y-1">
              <li>• Mail server configured for {config.domain || 'your domain'}</li>
              <li>• DKIM keys generated for email signing</li>
              <li>• DNS records provided for SPF, DKIM, DMARC</li>
              <li>• You can start creating email users immediately</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )

  const renderStep2 = () => (
    <div className="space-y-6">
      <p className="text-gray-600">Configure security features for this domain:</p>

      <div className="space-y-4">
        {/* Spam Filter */}
        <label className="flex items-start gap-3 p-4 border border-gray-200 rounded-lg hover:border-gray-300 cursor-pointer">
          <input
            type="checkbox"
            checked={config.spam_filter_enabled}
            onChange={(e) => setConfig({ ...config, spam_filter_enabled: e.target.checked })}
            className="mt-1 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
          />
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-purple-600" />
              <span className="font-medium">SpamAssassin Filter</span>
            </div>
            <p className="text-sm text-gray-600 mt-1">
              Bayesian filtering, Pyzor, Razor, and DCC network checks. 
              Blocks 95%+ of spam.
            </p>
          </div>
        </label>

        {/* Virus Scanning */}
        <label className="flex items-start gap-3 p-4 border border-gray-200 rounded-lg hover:border-gray-300 cursor-pointer">
          <input
            type="checkbox"
            checked={config.virus_scan_enabled}
            onChange={(e) => setConfig({ ...config, virus_scan_enabled: e.target.checked })}
            className="mt-1 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
          />
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-red-600" />
              <span className="font-medium">ClamAV Virus Scanning</span>
            </div>
            <p className="text-sm text-gray-600 mt-1">
              Real-time virus and malware scanning with automatic signature updates.
            </p>
          </div>
        </label>

        {/* DKIM */}
        <label className="flex items-start gap-3 p-4 border border-gray-200 rounded-lg hover:border-gray-300 cursor-pointer">
          <input
            type="checkbox"
            checked={config.dkim_enabled}
            onChange={(e) => setConfig({ ...config, dkim_enabled: e.target.checked })}
            className="mt-1 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
          />
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <Check className="w-5 h-5 text-green-600" />
              <span className="font-medium">DKIM Signing</span>
            </div>
            <p className="text-sm text-gray-600 mt-1">
              Cryptographic email signing to prove authenticity. 
              Required for good deliverability.
            </p>
          </div>
        </label>

        {/* DMARC */}
        <label className="flex items-start gap-3 p-4 border border-gray-200 rounded-lg hover:border-gray-300 cursor-pointer">
          <input
            type="checkbox"
            checked={config.dmarc_enabled}
            onChange={(e) => setConfig({ ...config, dmarc_enabled: e.target.checked })}
            className="mt-1 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
          />
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-blue-600" />
              <span className="font-medium">DMARC Policy</span>
            </div>
            <p className="text-sm text-gray-600 mt-1">
              Domain-based Message Authentication. 
              Protects against domain spoofing.
            </p>
          </div>
        </label>

        {/* LLM Classification */}
        <label className="flex items-start gap-3 p-4 border border-gray-200 rounded-lg hover:border-gray-300 cursor-pointer">
          <input
            type="checkbox"
            checked={config.llm_enabled}
            onChange={(e) => setConfig({ ...config, llm_enabled: e.target.checked })}
            className="mt-1 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
          />
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-blue-600" />
              <span className="font-medium">AI Email Classification (LLM)</span>
            </div>
            <p className="text-sm text-gray-600 mt-1">
              Advanced email categorization using GPT-4 or Claude. 
              Can classify emails as important, newsletter, social, promotional, etc.
            </p>
          </div>
        </label>
      </div>
    </div>
  )

  const renderStep3 = () => {
    if (!config.llm_enabled) {
      return (
        <div className="text-center py-8">
          <Check className="w-16 h-16 text-green-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium">Ready to create!</h3>
          <p className="text-gray-600 mt-2">
            Your mail domain {config.domain} will be configured with the selected security features.
          </p>
        </div>
      )
    }

    return (
      <div className="space-y-6">
        <p className="text-gray-600">Configure LLM email classification:</p>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Provider
            </label>
            <select
              value={config.llm_config.provider}
              onChange={(e) => setConfig({
                ...config,
                llm_config: { ...config.llm_config, provider: e.target.value }
              })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic Claude</option>
              <option value="local">Local Model</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Model
            </label>
            <select
              value={config.llm_config.model}
              onChange={(e) => setConfig({
                ...config,
                llm_config: { ...config.llm_config, model: e.target.value }
              })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="gpt-4">GPT-4</option>
              <option value="gpt-4-turbo">GPT-4 Turbo</option>
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
            </select>
          </div>
        </div>

        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-sm text-yellow-800">
            <strong>Note:</strong> LLM classification requires an API key to be configured 
            in the instance settings. Emails are processed securely and not stored by the LLM provider.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div>
      <button
        onClick={() => navigate('/mail')}
        className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Mail
      </button>

      <h2 className="text-2xl font-bold text-gray-900 mb-6">Add Mail Domain</h2>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-4 mb-6">
          {[1, 2, 3].map((s) => (
            <div
              key={s}
              className={`flex items-center gap-2 ${
                s < step ? 'text-green-600' : s === step ? 'text-primary-600' : 'text-gray-400'
              }`}
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                s < step ? 'bg-green-100' : s === step ? 'bg-primary-100' : 'bg-gray-100'
              }`}>
                {s < step ? <Check className="w-5 h-5" /> : s}
              </div>
              <span className="text-sm hidden sm:block">
                {s === 1 && 'Domain'}
                {s === 2 && 'Security'}
                {s === 3 && 'LLM'}
              </span>
            </div>
          ))}
        </div>

        {step === 1 && renderStep1()}
        {step === 2 && renderStep2()}
        {step === 3 && renderStep3()}

        <div className="flex justify-between mt-8 pt-6 border-t border-gray-200">
          <button
            onClick={() => step > 1 ? setStep(step - 1) : navigate('/mail')}
            className="px-4 py-2 text-gray-700 hover:text-gray-900"
          >
            {step > 1 ? 'Back' : 'Cancel'}
          </button>

          <button
            onClick={() => {
              if (step < 3) {
                setStep(step + 1)
              } else {
                handleSubmit()
              }
            }}
            disabled={step === 1 && !config.domain}
            className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
          >
            {step < 3 ? 'Continue' : 'Create Domain'}
          </button>
        </div>
      </div>
    </div>
  )
}
