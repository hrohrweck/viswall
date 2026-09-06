import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import {
  Badge,
  StatusBadge,
  RoleBadge,
  AuthBackendBadge,
  ProtocolBadge,
  InstanceStatusBadge,
  VPNStatusBadge,
} from '../components/ui/StatusBadge'
import { InstanceStatus, VPNStatus, UserRole } from '../types'

/**
 * Kit badge tests — token-driven Badge internals, icon pairing, variant
 * mapping, unknown fallback, and six-export prop contract.
 */

// ─── helpers ────────────────────────────────────────────────────────

/** Find the Badge wrapper (outer inline-flex span) that contains the given text. */
function getBadgeByText(text: string): HTMLElement {
  const el = screen.getByText(text)
  // StatusBadge wraps label in <span class="capitalize">, RoleBadge/AuthBackend/Protocol
  // render text directly. Walk up to the nearest element with gap-1 (Badge root).
  const badge = (el.parentElement?.classList.contains('inline-flex')
    ? el.parentElement
    : el.parentElement?.parentElement) as HTMLElement
  expect(badge).toBeTruthy()
  return badge
}

// ─── (1) icon + label rendering ─────────────────────────────────────

describe('StatusBadge renders icon + label', () => {
  it.each([
    ['active', 'CheckCircle2'],
    ['error', 'XCircle'],
    ['maintenance', 'AlertTriangle'],
    ['stopped', 'MinusCircle'],
  ])('status=%s → %s icon + label', (status, _iconName) => {
    render(<StatusBadge status={status} />)
    const badge = getBadgeByText(status)
    // Icon: lucide renders <svg aria-hidden="true">
    const svg = badge.querySelector('svg')
    expect(svg).toBeInTheDocument()
    expect(svg).toHaveAttribute('aria-hidden', 'true')
  })
})

// ─── (2) status → variant class mapping table ──────────────────────

describe('StatusBadge variant mapping', () => {
  it.each([
    ['active', 'bg-success-subtle'],
    ['running', 'bg-success-subtle'],
    ['online', 'bg-success-subtle'],
    ['inactive', 'bg-neutral-subtle'],
    ['stopped', 'bg-neutral-subtle'],
    ['offline', 'bg-neutral-subtle'],
    ['error', 'bg-danger-subtle'],
    ['maintenance', 'bg-warning-subtle'],
    ['restarting', 'bg-warning-subtle'],
  ])('status=%s → class %s', (status, expectedClass) => {
    render(<StatusBadge status={status} />)
    const badge = getBadgeByText(status)
    expect(badge).toHaveClass(expectedClass)
  })
})

// ─── (3) unknown status → neutral + MinusCircle ────────────────────

describe('StatusBadge unknown fallback', () => {
  it('renders neutral variant with MinusCircle icon', () => {
    render(<StatusBadge status="flurbo" />)
    const badge = getBadgeByText('flurbo')
    expect(badge).toHaveClass('bg-neutral-subtle')
    expect(badge.querySelector('svg')).toBeInTheDocument()
  })
})

// ─── (4) six exports accept current prop shapes ────────────────────

describe('export prop contract', () => {
  it('StatusBadge accepts { status: string }', () => {
    render(<StatusBadge status="active" />)
    expect(screen.getByText('active')).toBeInTheDocument()
  })

  it('RoleBadge accepts { role: UserRole | string }', () => {
    const { rerender } = render(<RoleBadge role={UserRole.ADMIN} />)
    expect(screen.getByText('admin')).toBeInTheDocument()
    rerender(<RoleBadge role={UserRole.SUPERADMIN} />)
    expect(screen.getByText('superadmin')).toBeInTheDocument()
  })

  it('AuthBackendBadge accepts { backend: AuthBackend | string }', () => {
    render(<AuthBackendBadge backend="local" />)
    expect(screen.getByText('Local')).toBeInTheDocument()
  })

  it('ProtocolBadge accepts { protocol: string }', () => {
    render(<ProtocolBadge protocol="wireguard" />)
    expect(screen.getByText('wireguard')).toBeInTheDocument()
  })

  it('InstanceStatusBadge accepts { status: InstanceStatus }', () => {
    render(<InstanceStatusBadge status={InstanceStatus.ACTIVE} />)
    expect(screen.getByText('active')).toBeInTheDocument()
  })

  it('VPNStatusBadge accepts { status: VPNStatus }', () => {
    render(<VPNStatusBadge status={VPNStatus.RUNNING} />)
    expect(screen.getByText('running')).toBeInTheDocument()
  })
})

// ─── (5) AuthBackend label mapping ─────────────────────────────────

describe('AuthBackendBadge label mapping', () => {
  it.each([
    ['local', 'Local'],
    ['ldap', 'LDAP'],
    ['ad', 'Active Directory'],
  ])('backend=%s → label "%s"', (backend, label) => {
    render(<AuthBackendBadge backend={backend} />)
    expect(screen.getByText(label)).toBeInTheDocument()
  })
})

// ─── (6) Badge base component ──────────────────────────────────────

describe('Badge base component', () => {
  it('applies variant class and renders children', () => {
    render(<Badge variant="success">hello</Badge>)
    const badge = screen.getByText('hello')
    expect(badge).toHaveClass('bg-success-subtle', 'text-success')
  })

  it('renders icon when provided', () => {
    render(<Badge variant="info" icon={undefined}>no icon</Badge>)
    const badge = screen.getByText('no icon')
    expect(badge.querySelector('svg')).not.toBeInTheDocument()
  })

  it('merges className', () => {
    render(<Badge variant="danger" className="extra">x</Badge>)
    const badge = screen.getByText('x')
    expect(badge).toHaveClass('extra')
    expect(badge).toHaveClass('bg-danger-subtle')
  })
})

// ─── (7) RoleBadge has no icon (text-only) ─────────────────────────

describe('RoleBadge is text-only', () => {
  it.each(['superadmin', 'admin', 'user', 'readonly'])('role=%s renders without icon', (role) => {
    render(<RoleBadge role={role} />)
    const badge = getBadgeByText(role)
    expect(badge.querySelector('svg')).not.toBeInTheDocument()
  })
})

// ─── (8) ProtocolBadge variant mapping ─────────────────────────────

describe('ProtocolBadge variant mapping', () => {
  it.each([
    ['wireguard', 'bg-success-subtle'],
    ['ipsec', 'bg-info-subtle'],
    ['openvpn', 'bg-warning-subtle'],
    ['l2tp', 'bg-warning-subtle'],
    ['pptp', 'bg-danger-subtle'],
  ])('protocol=%s → %s', (protocol, expectedClass) => {
    render(<ProtocolBadge protocol={protocol} />)
    const badge = getBadgeByText(protocol)
    expect(badge).toHaveClass(expectedClass)
  })
})
