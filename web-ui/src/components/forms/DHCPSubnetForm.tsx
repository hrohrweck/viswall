import { useState } from 'react'
import { Button, Field, Input, Select } from '../ui'
import { DHCPSubnetType } from '../../types'
import type { DHCPSubnetCreate } from '../../types'

interface DHCPSubnetFormProps {
  loading: boolean
  onSubmit: (payload: DHCPSubnetCreate) => void
}

export function DHCPSubnetForm({ loading, onSubmit }: DHCPSubnetFormProps) {
  const [name, setName] = useState('lan-subnet')
  const [subnet, setSubnet] = useState('192.168.10.0/24')
  const [type, setType] = useState(DHCPSubnetType.V4)
  const [routers, setRouters] = useState('192.168.10.1')
  const [dnsServers, setDnsServers] = useState('192.168.10.53')
  const [leaseMin, setLeaseMin] = useState(300)
  const [leaseDefault, setLeaseDefault] = useState(3600)
  const [leaseMax, setLeaseMax] = useState(7200)
  const [delegatedPrefixLength, setDelegatedPrefixLength] = useState('')

  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault()
        onSubmit({
          name,
          subnet,
          type,
          routers: routers.split(',').map((item) => item.trim()).filter(Boolean),
          dns_servers: dnsServers.split(',').map((item) => item.trim()).filter(Boolean),
          lease_time_min: leaseMin,
          lease_time_default: leaseDefault,
          lease_time_max: leaseMax,
          delegated_prefix_length: delegatedPrefixLength
            ? Number(delegatedPrefixLength)
            : undefined,
        })
      }}
    >
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Field label="Name">
          <Input value={name} onChange={(event) => setName(event.target.value)} />
        </Field>
        <Field label="Type">
          <Select
            value={type}
            onChange={(event) => setType(event.target.value as DHCPSubnetType)}
          >
            <option value={DHCPSubnetType.V4}>IPv4</option>
            <option value={DHCPSubnetType.V6}>IPv6</option>
          </Select>
        </Field>
      </div>

      <Field label="Subnet CIDR">
        <Input mono value={subnet} onChange={(event) => setSubnet(event.target.value)} />
      </Field>

      <Field label="Routers (comma separated)">
        <Input mono value={routers} onChange={(event) => setRouters(event.target.value)} />
      </Field>

      <Field label="DNS servers (comma separated)">
        <Input mono value={dnsServers} onChange={(event) => setDnsServers(event.target.value)} />
      </Field>

      <div className="grid grid-cols-3 gap-3">
        <Field label="Min">
          <Input
            type="number"
            value={leaseMin}
            onChange={(event) => setLeaseMin(Number(event.target.value))}
          />
        </Field>
        <Field label="Default">
          <Input
            type="number"
            value={leaseDefault}
            onChange={(event) => setLeaseDefault(Number(event.target.value))}
          />
        </Field>
        <Field label="Max">
          <Input
            type="number"
            value={leaseMax}
            onChange={(event) => setLeaseMax(Number(event.target.value))}
          />
        </Field>
      </div>

      {type === DHCPSubnetType.V6 ? (
        <Field label="Delegated Prefix Length (optional)">
          <Input
            value={delegatedPrefixLength}
            onChange={(event) => setDelegatedPrefixLength(event.target.value)}
            placeholder="64"
          />
        </Field>
      ) : null}

      <div className="flex justify-end">
        <Button type="submit" loading={loading}>
          Create Subnet
        </Button>
      </div>
    </form>
  )
}
