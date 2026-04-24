import { InstanceStatus, VPNStatus, UserRole, AuthBackend } from '../../types'

type BadgeVariant = 'success' | 'danger' | 'warning' | 'info' | 'neutral'

function getBadgeClasses(variant: BadgeVariant): string {
  const map: Record<BadgeVariant, string> = {
    success: 'bg-green-100 text-green-800',
    danger: 'bg-red-100 text-red-800',
    warning: 'bg-yellow-100 text-yellow-800',
    info: 'bg-blue-100 text-blue-800',
    neutral: 'bg-gray-100 text-gray-800',
  }
  return map[variant]
}

export function StatusBadge({ status }: { status: string }) {
  const variants: Record<string, BadgeVariant> = {
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

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${getBadgeClasses(variants[status] || 'neutral')}`}>
      {status}
    </span>
  )
}

export function RoleBadge({ role }: { role: UserRole | string }) {
  const variants: Record<string, BadgeVariant> = {
    superadmin: 'danger',
    admin: 'warning',
    user: 'info',
    readonly: 'neutral',
  }

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getBadgeClasses(variants[role] || 'neutral')}`}>
      {role}
    </span>
  )
}

export function AuthBackendBadge({ backend }: { backend: AuthBackend | string }) {
  const variants: Record<string, BadgeVariant> = {
    local: 'info',
    ldap: 'warning',
    ad: 'success',
  }
  const labels: Record<string, string> = {
    local: 'Local',
    ldap: 'LDAP',
    ad: 'Active Directory',
  }

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getBadgeClasses(variants[backend] || 'neutral')}`}>
      {labels[backend] || backend}
    </span>
  )
}

export function ProtocolBadge({ protocol }: { protocol: string }) {
  const variants: Record<string, BadgeVariant> = {
    wireguard: 'success',
    ipsec: 'info',
    openvpn: 'warning',
    l2tp: 'warning',
    pptp: 'danger',
  }

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${getBadgeClasses(variants[protocol] || 'neutral')}`}>
      {protocol}
    </span>
  )
}

export function InstanceStatusBadge({ status }: { status: InstanceStatus }) {
  return <StatusBadge status={status} />
}

export function VPNStatusBadge({ status }: { status: VPNStatus }) {
  return <StatusBadge status={status} />
}
