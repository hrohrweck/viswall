import { useState } from 'react'
import { Button, Checkbox, Field, Input, Select } from '../ui'
import { DHCPHAMode } from '../../types'
import type { DHCPServerCreate } from '../../types'

interface DHCPServerFormProps {
  loading: boolean
  onSubmit: (payload: DHCPServerCreate) => void
}

export function DHCPServerForm({ loading, onSubmit }: DHCPServerFormProps) {
  const [name, setName] = useState('kea-dhcp-1')
  const [dhcpv4Enabled, setDhcpv4Enabled] = useState(true)
  const [dhcpv6Enabled, setDhcpv6Enabled] = useState(false)
  const [haEnabled, setHaEnabled] = useState(false)
  const [haMode, setHaMode] = useState(DHCPHAMode.HOT_STANDBY)
  const [haPeerAddress, setHaPeerAddress] = useState('')

  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault()
        onSubmit({
          name,
          dhcpv4_enabled: dhcpv4Enabled,
          dhcpv6_enabled: dhcpv6Enabled,
          ha_enabled: haEnabled,
          ha_mode: haMode,
          ha_peer_address: haEnabled ? haPeerAddress : undefined,
        })
      }}
    >
      <Field label="Name">
        <Input
          value={name}
          onChange={(event) => setName(event.target.value)}
        />
      </Field>

      <div className="flex items-center gap-6">
        <label className="inline-flex items-center gap-2 text-sm cursor-pointer">
          <Checkbox
            checked={dhcpv4Enabled}
            onChange={(event) => setDhcpv4Enabled(event.target.checked)}
          />
          DHCPv4
        </label>
        <label className="inline-flex items-center gap-2 text-sm cursor-pointer">
          <Checkbox
            checked={dhcpv6Enabled}
            onChange={(event) => setDhcpv6Enabled(event.target.checked)}
          />
          DHCPv6
        </label>
      </div>

      <label className="inline-flex items-center gap-2 text-sm cursor-pointer">
        <Checkbox
          checked={haEnabled}
          onChange={(event) => setHaEnabled(event.target.checked)}
        />
        Enable HA
      </label>

      {haEnabled ? (
        <>
          <Field label="HA Mode">
            <Select
              value={haMode}
              onChange={(event) => setHaMode(event.target.value as DHCPHAMode)}
            >
              <option value={DHCPHAMode.HOT_STANDBY}>Hot standby</option>
              <option value={DHCPHAMode.LOAD_BALANCING}>Load balancing</option>
            </Select>
          </Field>
          <Field label="HA Peer Address">
            <Input
              mono
              value={haPeerAddress}
              onChange={(event) => setHaPeerAddress(event.target.value)}
              placeholder="10.0.0.2"
            />
          </Field>
        </>
      ) : null}

      <div className="flex justify-end">
        <Button type="submit" loading={loading}>
          Create Server
        </Button>
      </div>
    </form>
  )
}
