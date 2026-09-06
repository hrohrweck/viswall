import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Info,
  MinusCircle,
  type LucideIcon,
} from 'lucide-react'
import { cn } from '../../lib/utils'
import { InstanceStatus, VPNStatus, UserRole, AuthBackend } from '../../types'

/* ------------------------------------------------------------------ */
/* Badge — token-driven base component with optional icon pairing      */
/* ------------------------------------------------------------------ */

type BadgeVariant = 'success' | 'danger' | 'warning' | 'info' | 'neutral'

const variantClasses: Record<BadgeVariant, string> = {
  success: 'bg-success-subtle text-success',
  danger: 'bg-danger-subtle text-danger',
  warning: 'bg-warning-subtle text-warning',
  info: 'bg-info-subtle text-info',
  neutral: 'bg-neutral-subtle text-on-surface-muted',
}

interface BadgeProps {
  variant: BadgeVariant
  icon?: LucideIcon
  children: React.ReactNode
  className?: string
}

export function Badge({ variant, icon: Icon, children, className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium',
        variantClasses[variant],
        className,
      )}
    >
      {Icon && <Icon className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />}
      {children}
    </span>
  )
}

/* ------------------------------------------------------------------ */
/* Icon lookup by variant (used by status badges)                      */
/* ------------------------------------------------------------------ */

const variantIcon: Record<BadgeVariant, LucideIcon> = {
  success: CheckCircle2,
  danger: XCircle,
  warning: AlertTriangle,
  info: Info,
  neutral: MinusCircle,
}

/* ------------------------------------------------------------------ */
/* StatusBadge — icon + colour paired, label capitalised               */
/* ------------------------------------------------------------------ */

const statusVariants: Record<string, BadgeVariant> = {
  active: 'success',
  running: 'success',
  online: 'success',
  inactive: 'neutral',
  stopped: 'neutral',
  offline: 'neutral',
  error: 'danger',
  maintenance: 'warning',
  restarting: 'warning',
}

export function StatusBadge({ status }: { status: string }) {
  const variant = statusVariants[status] ?? 'neutral'
  return (
    <Badge variant={variant} icon={variantIcon[variant]}>
      <span className="capitalize">{status}</span>
    </Badge>
  )
}

/* ------------------------------------------------------------------ */
/* RoleBadge — text-only (roles are not operational statuses)           */
/* ------------------------------------------------------------------ */

const roleVariants: Record<string, BadgeVariant> = {
  superadmin: 'danger',
  admin: 'warning',
  user: 'info',
  readonly: 'neutral',
}

export function RoleBadge({ role }: { role: UserRole | string }) {
  const variant = roleVariants[role] ?? 'neutral'
  return <Badge variant={variant}>{role}</Badge>
}

/* ------------------------------------------------------------------ */
/* AuthBackendBadge — variant + label mapping (no icon)                */
/* ------------------------------------------------------------------ */

const authBackendVariants: Record<string, BadgeVariant> = {
  local: 'info',
  ldap: 'warning',
  ad: 'success',
}

const authBackendLabels: Record<string, string> = {
  local: 'Local',
  ldap: 'LDAP',
  ad: 'Active Directory',
}

export function AuthBackendBadge({ backend }: { backend: AuthBackend | string }) {
  const variant = authBackendVariants[backend] ?? 'neutral'
  return <Badge variant={variant}>{authBackendLabels[backend] || backend}</Badge>
}

/* ------------------------------------------------------------------ */
/* ProtocolBadge — variant + capitalize (no icon)                      */
/* ------------------------------------------------------------------ */

const protocolVariants: Record<string, BadgeVariant> = {
  wireguard: 'success',
  ipsec: 'info',
  openvpn: 'warning',
  l2tp: 'warning',
  pptp: 'danger',
}

export function ProtocolBadge({ protocol }: { protocol: string }) {
  const variant = protocolVariants[protocol] ?? 'neutral'
  return (
    <Badge variant={variant}>
      <span className="capitalize">{protocol}</span>
    </Badge>
  )
}

/* ------------------------------------------------------------------ */
/* Thin delegates — unchanged prop signatures                          */
/* ------------------------------------------------------------------ */

export function InstanceStatusBadge({ status }: { status: InstanceStatus }) {
  return <StatusBadge status={status} />
}

export function VPNStatusBadge({ status }: { status: VPNStatus }) {
  return <StatusBadge status={status} />
}
