import { useState } from 'react'
import { Button, Field, Input } from '../ui'
import { DHCPSubnetType } from '../../types'
import type { DHCPReservationCreate } from '../../types'

interface DHCPReservationFormProps {
  subnetType: DHCPSubnetType
  loading: boolean
  onSubmit: (payload: DHCPReservationCreate) => void
}

export function DHCPReservationForm({
  subnetType,
  loading,
  onSubmit,
}: DHCPReservationFormProps) {
  const [hostname, setHostname] = useState('host-01')
  const [ipAddress, setIpAddress] = useState(
    subnetType === DHCPSubnetType.V4 ? '192.168.10.10' : '2001:db8::10',
  )
  const [hwAddress, setHwAddress] = useState(
    subnetType === DHCPSubnetType.V4
      ? '52:54:00:12:34:56'
      : '00:03:00:01:52:54:00:12:34:56',
  )

  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault()
        onSubmit({
          hostname,
          ip_address: ipAddress,
          hw_address: hwAddress,
          type: subnetType,
        })
      }}
    >
      <Field label="Hostname">
        <Input value={hostname} onChange={(event) => setHostname(event.target.value)} />
      </Field>
      <Field label="IP Address">
        <Input mono value={ipAddress} onChange={(event) => setIpAddress(event.target.value)} />
      </Field>
      <Field label={subnetType === DHCPSubnetType.V4 ? 'MAC Address' : 'DUID'}>
        <Input mono value={hwAddress} onChange={(event) => setHwAddress(event.target.value)} />
      </Field>
      <div className="flex justify-end">
        <Button type="submit" loading={loading}>
          Create Reservation
        </Button>
      </div>
    </form>
  )
}
