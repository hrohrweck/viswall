import { describe, it, expect } from 'vitest'
import { VPNProtocol, UserRole, InstanceStatus, FirewallAction } from '../types'

describe('TypeScript types', () => {
  it('VPNProtocol enum has expected values', () => {
    expect(VPNProtocol.WIREGUARD).toBe('wireguard')
    expect(VPNProtocol.IPSEC).toBe('ipsec')
    expect(VPNProtocol.OPENVPN).toBe('openvpn')
  })

  it('UserRole enum has expected values', () => {
    expect(UserRole.SUPERADMIN).toBe('superadmin')
    expect(UserRole.ADMIN).toBe('admin')
    expect(UserRole.USER).toBe('user')
    expect(UserRole.READONLY).toBe('readonly')
  })

  it('InstanceStatus enum has expected values', () => {
    expect(InstanceStatus.ACTIVE).toBe('active')
    expect(InstanceStatus.INACTIVE).toBe('inactive')
    expect(InstanceStatus.ERROR).toBe('error')
  })

  it('FirewallAction enum has expected values', () => {
    expect(FirewallAction.ACCEPT).toBe('accept')
    expect(FirewallAction.DROP).toBe('drop')
    expect(FirewallAction.REJECT).toBe('reject')
  })
})

describe('formatBytes', () => {
  it('formats bytes correctly', async () => {
    const { formatBytes } = await import('../utils/format')
    expect(formatBytes(0)).toBe('0 B')
    expect(formatBytes(1024)).toBe('1 KB')
    expect(formatBytes(1048576)).toBe('1 MB')
    expect(formatBytes(1073741824)).toBe('1 GB')
  })
})
