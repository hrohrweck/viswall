import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeAll, describe, expect, it, vi } from 'vitest'
import { FirewallRuleForm } from '../components/forms/FirewallRuleForm'
import { InstanceCreateForm } from '../components/forms/InstanceCreateForm'
import { UserCreateForm } from '../components/forms/UserCreateForm'
import { RoutingRuleForm } from '../components/forms/RoutingRuleForm'
import { DHCPServerForm } from '../components/forms/DHCPServerForm'
import { DHCPReservationForm } from '../components/forms/DHCPReservationForm'
import { DNSZoneForm } from '../components/forms/DNSZoneForm'
import { MailboxForm } from '../components/forms/MailboxForm'
import { AuthBackend, DHCPSubnetType, DNSZoneType, UserRole } from '../types'

// Radix Switch (RoutingRuleForm) touches ResizeObserver via its internal size hooks.
beforeAll(() => {
  Object.defineProperty(globalThis, 'ResizeObserver', {
    value: class {
      observe() {}
      unobserve() {}
      disconnect() {}
    },
    writable: true,
    configurable: true,
  })
})

describe('Forms — react-hook-form + zod validation', () => {
  /* ── 1. Invalid IP blocks submit + error text ─────────────────────────── */
  it('FirewallRuleForm blocks submit and shows an error for an invalid source IP', async () => {
    const user = userEvent.setup()
    const spy = vi.fn().mockResolvedValue(undefined)
    render(<FirewallRuleForm onSubmit={spy} onCancel={vi.fn()} loading={false} />)

    await user.type(screen.getByRole('textbox', { name: 'Rule Name' }), 'Block SMB')
    await user.selectOptions(screen.getByRole('combobox', { name: 'Source Type' }), 'ip')
    await user.type(screen.getByRole('textbox', { name: 'Source Value' }), 'not-an-ip')

    await user.click(screen.getByRole('button', { name: 'Save Rule' }))

    expect(await screen.findByText('Enter a valid IP address')).toBeInTheDocument()
    expect(spy).not.toHaveBeenCalled()
  })

  /* ── 2. Invalid MAC blocks submit + error text ────────────────────────── */
  it('DHCPReservationForm blocks submit and shows an error for an invalid MAC address', async () => {
    const user = userEvent.setup()
    const spy = vi.fn()
    render(
      <DHCPReservationForm subnetType={DHCPSubnetType.V4} loading={false} onSubmit={spy} />,
    )

    await user.clear(screen.getByRole('textbox', { name: 'MAC Address' }))
    await user.type(screen.getByRole('textbox', { name: 'MAC Address' }), 'zz:zz:zz:zz:zz:zz')
    await user.click(screen.getByRole('button', { name: 'Create Reservation' }))

    expect(await screen.findByText(/Enter a valid MAC address/i)).toBeInTheDocument()
    expect(spy).not.toHaveBeenCalled()
  })

  /* ── 3. Invalid email blocks submit + error text ──────────────────────── */
  it('UserCreateForm blocks submit and shows an error for an invalid email', async () => {
    const user = userEvent.setup()
    const spy = vi.fn().mockResolvedValue(undefined)
    render(<UserCreateForm instances={[]} onSubmit={spy} onCancel={vi.fn()} loading={false} />)

    await user.type(screen.getByRole('textbox', { name: 'Username' }), 'jane')
    await user.type(screen.getByRole('textbox', { name: 'Email' }), 'not-an-email')
    await user.click(screen.getByRole('button', { name: 'Create User' }))

    expect(await screen.findByText('Enter a valid email address')).toBeInTheDocument()
    expect(spy).not.toHaveBeenCalled()
  })

  /* ── 4. Invalid port range blocks submit + error text ─────────────────── */
  it('FirewallRuleForm blocks submit and shows an error for an out-of-range port', async () => {
    const user = userEvent.setup()
    const spy = vi.fn().mockResolvedValue(undefined)
    render(<FirewallRuleForm onSubmit={spy} onCancel={vi.fn()} loading={false} />)

    await user.type(screen.getByRole('textbox', { name: 'Rule Name' }), 'Allow HTTPS')
    await user.type(screen.getByRole('textbox', { name: 'Ports' }), '70000')
    await user.click(screen.getByRole('button', { name: 'Save Rule' }))

    expect(await screen.findByText('Enter ports as 80, 443 or 1000-2000')).toBeInTheDocument()
    expect(spy).not.toHaveBeenCalled()
  })

  /* ── 5. Invalid HA peer IP blocks submit ──────────────────────────────── */
  it('DHCPServerForm blocks submit when HA is enabled without a valid peer IP', async () => {
    const user = userEvent.setup()
    const spy = vi.fn()
    render(<DHCPServerForm loading={false} onSubmit={spy} />)

    await user.click(screen.getByLabelText('Enable HA'))
    await user.click(screen.getByRole('button', { name: 'Create Server' }))

    expect(await screen.findByText('Enter a valid peer IP address')).toBeInTheDocument()
    expect(spy).not.toHaveBeenCalled()
  })

  /* ── 6. Valid payload deep-equal (submit spy) ─────────────────────────── */
  it('RoutingRuleForm submits a payload deep-equal to the pre-validation shape', async () => {
    const user = userEvent.setup()
    const spy = vi.fn()
    render(<RoutingRuleForm onSubmit={spy} onCancel={vi.fn()} loading={false} />)

    await user.type(screen.getByRole('textbox', { name: 'Name' }), 'Route DMZ to WAN')
    await user.click(screen.getByRole('button', { name: 'Create' }))

    await waitFor(() => expect(spy).toHaveBeenCalledTimes(1))
    expect(spy.mock.calls[0][0]).toStrictEqual({
      name: 'Route DMZ to WAN',
      enabled: true,
      source_network: undefined,
      dest_network: undefined,
      service: undefined,
      inbound_interface: undefined,
      gateway: undefined,
      outbound_interface: undefined,
      mark: undefined,
      order_index: undefined,
    })
  })

  /* ── 7. Error clears once the field is corrected ──────────────────────── */
  it('UserCreateForm clears the email error once the address is corrected', async () => {
    const user = userEvent.setup()
    const spy = vi.fn().mockResolvedValue(undefined)
    render(<UserCreateForm instances={[]} onSubmit={spy} onCancel={vi.fn()} loading={false} />)

    await user.type(screen.getByRole('textbox', { name: 'Username' }), 'jane')
    await user.type(screen.getByRole('textbox', { name: 'Email' }), 'not-an-email')
    await user.click(screen.getByRole('button', { name: 'Create User' }))
    expect(await screen.findByText('Enter a valid email address')).toBeInTheDocument()

    await user.clear(screen.getByRole('textbox', { name: 'Email' }))
    await user.type(screen.getByRole('textbox', { name: 'Email' }), 'jane@example.com')
    await user.click(screen.getByRole('button', { name: 'Create User' }))

    await waitFor(() => expect(spy).toHaveBeenCalledTimes(1))
    expect(screen.queryByText('Enter a valid email address')).not.toBeInTheDocument()
    expect(spy.mock.calls[0][0]).toStrictEqual({
      username: 'jane',
      email: 'jane@example.com',
      'password': undefined,
      role: UserRole.USER,
      auth_backend: AuthBackend.LOCAL,
      instances: [],
    })
  })

  /* ── 8. aria-invalid is wired on the failing control ──────────────────── */
  it('UserCreateForm marks the failing input with aria-invalid', async () => {
    const user = userEvent.setup()
    const spy = vi.fn().mockResolvedValue(undefined)
    render(<UserCreateForm instances={[]} onSubmit={spy} onCancel={vi.fn()} loading={false} />)

    await user.type(screen.getByRole('textbox', { name: 'Username' }), 'jane')
    await user.type(screen.getByRole('textbox', { name: 'Email' }), 'not-an-email')
    await user.click(screen.getByRole('button', { name: 'Create User' }))

    await screen.findByText('Enter a valid email address')
    expect(screen.getByRole('textbox', { name: 'Email' })).toHaveAttribute('aria-invalid', 'true')
    expect(screen.getByRole('textbox', { name: 'Username' })).not.toHaveAttribute('aria-invalid')
  })

  /* ── 9. DNS happy path: default values pass validation ────────────────── */
  it('DNSZoneForm submits the default zone payload unchanged', async () => {
    const user = userEvent.setup()
    const spy = vi.fn().mockResolvedValue(undefined)
    render(
      <DNSZoneForm
        zoneTypeOptions={[DNSZoneType.MASTER, DNSZoneType.SLAVE]}
        loading={false}
        onSubmit={spy}
      />,
    )

    await user.click(screen.getByRole('button', { name: 'Create Zone' }))

    await waitFor(() => expect(spy).toHaveBeenCalledTimes(1))
    expect(spy.mock.calls[0][0]).toStrictEqual({
      name: 'example.internal',
      zone_type: DNSZoneType.MASTER,
      dnssec_enabled: false,
    })
  })

  /* ── 10. Mail happy path: local part + optional fields ────────────────── */
  it('MailboxForm submits { username, full_name: undefined, password omitted }', async () => {
    const user = userEvent.setup()
    const spy = vi.fn()
    render(<MailboxForm domain="example.com" onSubmit={spy} onCancel={vi.fn()} />)

    await user.type(screen.getByPlaceholderText('user'), 'jane')
    await user.click(screen.getByRole('button', { name: 'Create' }))

    await waitFor(() => expect(spy).toHaveBeenCalledTimes(1))
    expect(spy.mock.calls[0][0]).toStrictEqual({
      username: 'jane',
      full_name: undefined,
      'password': undefined,
    })
  })

  /* ── 11. Instance hostname validation (kit rewrite parity) ────────────── */
  it('InstanceCreateForm blocks submit for an invalid hostname and accepts a valid one', async () => {
    const user = userEvent.setup()
    const spy = vi.fn().mockResolvedValue(undefined)
    render(<InstanceCreateForm onSubmit={spy} onCancel={vi.fn()} loading={false} />)

    await user.type(screen.getByRole('textbox', { name: 'Name' }), 'Edge Berlin')
    await user.type(screen.getByRole('textbox', { name: 'Hostname' }), 'not a hostname')
    await user.click(screen.getByRole('button', { name: 'Create Instance' }))

    expect(await screen.findByText(/Enter a valid hostname/i)).toBeInTheDocument()
    expect(spy).not.toHaveBeenCalled()

    await user.clear(screen.getByRole('textbox', { name: 'Hostname' }))
    await user.type(screen.getByRole('textbox', { name: 'Hostname' }), 'edge-berlin-02')
    await user.click(screen.getByRole('button', { name: 'Create Instance' }))

    await waitFor(() => expect(spy).toHaveBeenCalledTimes(1))
    expect(spy.mock.calls[0][0]).toStrictEqual({
      name: 'Edge Berlin',
      hostname: 'edge-berlin-02',
      capabilities: [],
    })
  })
})
