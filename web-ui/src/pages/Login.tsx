import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shield, AlertTriangle } from 'lucide-react'
import { useAuthStore } from '../stores/auth'
import { useLogin } from '../hooks/useApi'
import { Field } from '../components/ui/Field'
import { Input } from '../components/ui/Input'
import { Checkbox } from '../components/ui/Switch'
import { Button } from '../components/ui/Button'
import { getErrMsg } from '../lib/utils'

/**
 * Sign-in page — split-screen layout.
 *
 * LEFT (45%): deep-slate brand panel with Viswall shield, headline, subline,
 *   and live stats from useInstances/useMetricsOverview (when auth is present).
 *   The panel is scoped with className="dark" so all token classes resolve to
 *   their dark values without any `dark:` responsive pairs.
 *
 * RIGHT: centred sign-in form using the UI kit (Field, Input, Checkbox, Button).
 *   Uses the `useLogin` mutation hook — auth store set on success, error banner
 *   shown on failure via `getErrMsg`.
 */
export function Login() {
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const login = useLogin()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [staySignedIn, setStaySignedIn] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    login.mutate(
      { username, password },
      {
        onSuccess: (data) => {
          setAuth(data.access_token, data.user)
          navigate('/')
        },
        onError: (err) => {
          setError(getErrMsg(err))
        },
      },
    )
  }

  return (
    <div className="min-h-screen flex">
      {/* ── Left brand panel (45%, permanently dark) ──────────────────── */}
      <div className="hidden lg:flex lg:w-[45%] flex-col justify-between dark bg-surface p-10">
        <div>
          <div className="flex items-center gap-3 mb-12">
            <Shield className="w-8 h-8 text-primary" />
            <span className="text-xl font-semibold text-on-surface">
              Viswall
            </span>
          </div>
          <h1 className="text-3xl font-bold text-on-surface leading-tight mb-4">
            Security infrastructure,
            <br />
            one control plane.
          </h1>
          <p className="text-on-surface-muted text-sm leading-relaxed max-w-sm">
            Manage firewall rules, VPN servers, DNS, DHCP, mail, and QoS
            across every edge instance from a single dashboard.
          </p>
        </div>
        <p className="text-xs text-on-surface-muted font-mono">
          Viswall v1.0 &middot; Open-source security appliance platform
        </p>
      </div>

      {/* ── Right form panel ─────────────────────────────────────────── */}
      <div className="flex-1 flex items-center justify-center bg-surface p-8">
        <div className="w-full max-w-sm">
          {/* Mobile-only shield */}
          <div className="flex items-center gap-3 mb-8 lg:hidden">
            <Shield className="w-7 h-7 text-primary" />
            <span className="text-lg font-semibold text-on-surface">
              Viswall
            </span>
          </div>

          <h2 className="text-2xl font-semibold text-on-surface mb-1">
            Sign in
          </h2>
          <p className="text-sm text-on-surface-muted mb-8">
            Enter your credentials to access the control plane.
          </p>

          {/* Error banner */}
          {error && (
            <div
              className="mb-6 flex items-center gap-3 rounded-card bg-danger-subtle p-4 text-sm text-danger"
              role="alert"
            >
              <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden="true" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
            <Field label="Username" required>
              <Input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                required
              />
            </Field>

            <Field label="Password" required>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </Field>

            <label htmlFor="stay-signed-in" className="flex items-center gap-2 text-sm text-on-surface cursor-pointer select-none">
              <Checkbox
                id="stay-signed-in"
                checked={staySignedIn}
                onChange={(e) => setStaySignedIn(e.target.checked)}
              />
              Stay signed in
            </label>

            <Button
              type="submit"
              loading={login.isPending}
              className="w-full"
            >
              Sign in
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}
