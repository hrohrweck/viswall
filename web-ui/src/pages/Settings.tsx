import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  Save,
  Palette,
  Shield,
  Trash2,
  Plug,
  Bot,
  Server,
  Eye,
  EyeOff,
} from 'lucide-react'
import {
  useLDAPConfig,
  useUpdateLDAPConfig,
  useDeleteLDAPConfig,
  useTestLDAPConnection,
} from '../hooks/useApi'
import { useAuthStore } from '../stores/auth'
import { useThemeStore, type Theme } from '../stores/theme'
import {
  PageHeader,
  Card,
  CardHeader,
  CardBody,
  Field,
  Input,
  Button,
  LoadingSpinner,
  ConfirmDialog,
  toast,
} from '../components/ui'
import { getErrMsg } from '../lib/utils'
import { APP_INFO } from '../lib/appInfo'
import type { LDAPConfig } from '../types'

/* -------------------------------------------------------------------------- */
/*  Sub-navigation sections                                                   */
/* -------------------------------------------------------------------------- */

type Section = 'appearance' | 'authentication' | 'ai-providers' | 'system'

const SECTIONS: { key: Section; label: string }[] = [
  { key: 'appearance', label: 'Appearance' },
  { key: 'authentication', label: 'Authentication' },
  { key: 'ai-providers', label: 'AI Providers' },
  { key: 'system', label: 'System' },
]

/* -------------------------------------------------------------------------- */
/*  Password field with eye toggle                                            */
/* -------------------------------------------------------------------------- */

function PasswordField({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string
  value: string
  onChange: (v: string) => void
  placeholder?: string
}) {
  const [visible, setVisible] = useState(false)
  return (
    <Field label={label}>
      <div className="relative">
        <Input
          type={visible ? 'text' : 'password'}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="pr-10"
        />
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          className="absolute right-2 top-1/2 -translate-y-1/2 text-on-surface-muted hover:text-on-surface"
          aria-label={visible ? 'Hide password' : 'Show password'}
        >
          {visible ? <EyeOff size={16} /> : <Eye size={16} />}
        </button>
      </div>
    </Field>
  )
}

/* -------------------------------------------------------------------------- */
/*  Settings page                                                             */
/* -------------------------------------------------------------------------- */

export function Settings() {
  const { user } = useAuthStore()
  const isAdmin = user?.role === 'admin' || user?.role === 'superadmin'

  const { data: ldapConfig, isLoading: ldapLoading } = useLDAPConfig()
  const updateLDAP = useUpdateLDAPConfig()
  const deleteLDAP = useDeleteLDAPConfig()
  const testLDAP = useTestLDAPConnection()

  const { theme, setTheme } = useThemeStore()

  const [activeSection, setActiveSection] = useState<Section>('appearance')
  const [ldapForm, setLdapForm] = useState<LDAPConfig | null>(null)
  const [ldapTestResult, setLdapTestResult] = useState<{
    success: boolean
    message: string
  } | null>(null)
  const [confirmOpen, setConfirmOpen] = useState(false)

  useEffect(() => {
    if (ldapConfig) {
      setLdapForm(ldapConfig)
    } else if (ldapConfig === null) {
      setLdapForm({
        server_url: '',
        bind_dn: '',
        bind_password: '',
        base_dn: '',
        user_filter: '(objectClass=person)',
      })
    }
  }, [ldapConfig])

  /* -- LDAP handlers ------------------------------------------------------- */

  const handleSaveLDAP = async () => {
    if (!ldapForm) return
    await updateLDAP.mutateAsync(ldapForm)
    toast.success('Settings saved')
  }

  const handleTestLDAP = async () => {
    if (!ldapForm) return
    setLdapTestResult(null)
    try {
      const result = await testLDAP.mutateAsync(ldapForm)
      setLdapTestResult({
        success: result.message.toLowerCase().includes('success'),
        message: result.message,
      })
    } catch (err: unknown) {
      setLdapTestResult({ success: false, message: getErrMsg(err) })
    }
  }

  const handleDeleteLDAP = async () => {
    await deleteLDAP.mutateAsync()
    setConfirmOpen(false)
    toast.success('LDAP configuration removed')
  }

  /* -- Loading state ------------------------------------------------------- */

  if (ldapLoading) return <LoadingSpinner />

  /* -- Theme segmented options --------------------------------------------- */

  const themeOptions: Theme[] = ['light', 'dark', 'system']

  /* -- Section content ----------------------------------------------------- */

  function renderSection() {
    switch (activeSection) {
      case 'appearance':
        return (
          <Card>
            <CardHeader title="Appearance" />
            <CardBody>
              <div className="flex flex-col gap-2">
                <span className="text-sm font-medium text-on-surface">Theme</span>
                <div className="flex items-center gap-1 rounded-card border border-border p-1 w-fit">
                  {themeOptions.map((t) => (
                    <button
                      key={t}
                      onClick={() => setTheme(t)}
                      className={`px-4 py-1.5 rounded-md text-sm font-medium capitalize transition-colors ${
                        theme === t
                          ? 'bg-primary text-white'
                          : 'text-on-surface hover:bg-surface-elevated'
                      }`}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </div>
            </CardBody>
          </Card>
        )

      case 'authentication':
        return (
          <Card>
            <CardHeader title="LDAP / Active Directory" />
            <CardBody className="space-y-4">
              {!isAdmin ? (
                <p className="text-sm text-on-surface-muted">
                  Administrator access required to manage LDAP settings.
                </p>
              ) : ldapForm ? (
                <>
                  <Field label="Server URL">
                    <Input
                      mono
                      value={ldapForm.server_url}
                      onChange={(e) =>
                        setLdapForm({ ...ldapForm, server_url: e.target.value })
                      }
                      placeholder="ldap://localhost:389 or ldaps://ad.example.com:636"
                    />
                  </Field>

                  <Field label="Bind DN">
                    <Input
                      mono
                      value={ldapForm.bind_dn}
                      onChange={(e) =>
                        setLdapForm({ ...ldapForm, bind_dn: e.target.value })
                      }
                      placeholder="cn=admin,dc=example,dc=com"
                    />
                  </Field>

                  <PasswordField
                    label="Bind Password"
                    value={ldapForm.bind_password}
                    onChange={(v) =>
                      setLdapForm({ ...ldapForm, bind_password: v })
                    }
                    placeholder="Service account password"
                  />

                  <Field label="Base DN">
                    <Input
                      mono
                      value={ldapForm.base_dn}
                      onChange={(e) =>
                        setLdapForm({ ...ldapForm, base_dn: e.target.value })
                      }
                      placeholder="dc=example,dc=com"
                    />
                  </Field>

                  <Field label="User Filter">
                    <Input
                      value={ldapForm.user_filter}
                      onChange={(e) =>
                        setLdapForm({ ...ldapForm, user_filter: e.target.value })
                      }
                      placeholder="(objectClass=person)"
                    />
                  </Field>

                  <Field label="Group Filter" helper="Optional">
                    <Input
                      value={ldapForm.group_filter || ''}
                      onChange={(e) =>
                        setLdapForm({
                          ...ldapForm,
                          group_filter: e.target.value || undefined,
                        })
                      }
                      placeholder="(objectClass=groupOfNames)"
                    />
                  </Field>

                  {ldapTestResult && (
                    <div
                      className={`p-3 rounded-card text-sm ${
                        ldapTestResult.success
                          ? 'bg-success-subtle text-success'
                          : 'bg-danger-subtle text-danger'
                      }`}
                    >
                      {ldapTestResult.message}
                    </div>
                  )}

                  <div className="flex items-center justify-between pt-2">
                    {ldapConfig && (
                      <Button
                        variant="ghost"
                        icon={Trash2}
                        onClick={() => setConfirmOpen(true)}
                        className="text-danger hover:bg-danger-subtle"
                      >
                        Remove configuration
                      </Button>
                    )}
                    <div className="flex items-center gap-2 ml-auto">
                      <Button
                        variant="secondary"
                        icon={Plug}
                        onClick={handleTestLDAP}
                        loading={testLDAP.isPending}
                      >
                        Test connection
                      </Button>
                      <Button
                        icon={Save}
                        onClick={handleSaveLDAP}
                        loading={updateLDAP.isPending}
                      >
                        Save
                      </Button>
                    </div>
                  </div>
                </>
              ) : null}
            </CardBody>
          </Card>
        )

      case 'ai-providers':
        return (
          <Card>
            <CardHeader title="AI Providers" />
            <CardBody>
              <p className="text-sm text-on-surface-muted mb-3">
                Configure LLM providers and models for email classification and
                the assistant.
              </p>
              <Link
                to="/admin/llm"
                className="text-sm font-medium text-primary hover:underline"
              >
                Configure →
              </Link>
            </CardBody>
          </Card>
        )

      case 'system':
        return (
          <Card>
            <CardHeader title="System Information" />
            <CardBody>
              <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <dt className="text-sm font-medium text-on-surface-muted">
                    API Version
                  </dt>
                  <dd className="text-sm text-on-surface mt-1">
                    {APP_INFO.version}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-on-surface-muted">
                    Frontend Version
                  </dt>
                  <dd className="text-sm text-on-surface mt-1">
                    {APP_INFO.version}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-on-surface-muted">
                    Database
                  </dt>
                  <dd className="text-sm text-on-surface mt-1">
                    PostgreSQL 16 + Redis 7
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-on-surface-muted">
                    Migration
                  </dt>
                  <dd className="text-sm text-on-surface font-mono mt-1">
                    {APP_INFO.migration}
                  </dd>
                </div>
              </dl>
            </CardBody>
          </Card>
        )
    }
  }

  /* -- Render -------------------------------------------------------------- */

  return (
    <div>
      <PageHeader title="Settings" />

      <div className="mt-6 flex gap-6">
        {/* Left sub-nav — visible on lg+ */}
        <nav className="hidden lg:block w-[200px] shrink-0">
          <ul className="flex flex-col gap-1">
            {SECTIONS.map((s) => (
              <li key={s.key}>
                <button
                  onClick={() => setActiveSection(s.key)}
                  className={`w-full text-left px-3 py-2 rounded-card text-sm font-medium transition-colors ${
                    activeSection === s.key
                      ? 'bg-primary-subtle text-primary'
                      : 'text-on-surface-muted hover:text-on-surface hover:bg-surface-elevated'
                  }`}
                >
                  {s.label}
                </button>
              </li>
            ))}
          </ul>
        </nav>

        {/* Mobile section tabs — visible below lg */}
        <div className="lg:hidden mb-4 flex gap-1 overflow-x-auto">
          {SECTIONS.map((s) => (
            <button
              key={s.key}
              onClick={() => setActiveSection(s.key)}
              className={`px-3 py-1.5 rounded-card text-sm font-medium whitespace-nowrap transition-colors ${
                activeSection === s.key
                  ? 'bg-primary-subtle text-primary'
                  : 'text-on-surface-muted hover:text-on-surface hover:bg-surface-elevated'
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>

        {/* Right content */}
        <div className="flex-1 min-w-0">{renderSection()}</div>
      </div>

      {/* Confirm dialog for LDAP removal */}
      <ConfirmDialog
        open={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        onConfirm={handleDeleteLDAP}
        title="Remove LDAP configuration?"
        message="This will remove the LDAP/Active Directory integration."
        impact="Removes the LDAP configuration; directory users can no longer sign in."
        confirmLabel="Remove"
        loading={deleteLDAP.isPending}
      />
    </div>
  )
}
