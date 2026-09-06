import { useState } from 'react'
import { Button, Field, Input } from '../ui'
import { DHCPSubnetType } from '../../types'
import type { DHCPPoolCreate } from '../../types'

interface DHCPPoolFormProps {
  subnetType: DHCPSubnetType
  loading: boolean
  onSubmit: (payload: DHCPPoolCreate) => void
}

export function DHCPPoolForm({ subnetType, loading, onSubmit }: DHCPPoolFormProps) {
  const [startAddress, setStartAddress] = useState(
    subnetType === DHCPSubnetType.V4 ? '192.168.10.100' : '2001:db8::100',
  )
  const [endAddress, setEndAddress] = useState(
    subnetType === DHCPSubnetType.V4 ? '192.168.10.200' : '2001:db8::1ff',
  )

  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault()
        onSubmit({ start_address: startAddress, end_address: endAddress, type: subnetType })
      }}
    >
      <Field label="Start Address">
        <Input
          mono
          value={startAddress}
          onChange={(event) => setStartAddress(event.target.value)}
        />
      </Field>
      <Field label="End Address">
        <Input
          mono
          value={endAddress}
          onChange={(event) => setEndAddress(event.target.value)}
        />
      </Field>
      <div className="flex justify-end">
        <Button type="submit" loading={loading}>
          Create Pool
        </Button>
      </div>
    </form>
  )
}
