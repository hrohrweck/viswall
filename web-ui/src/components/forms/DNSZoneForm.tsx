import { useState } from 'react'
import { Field, Input, Select, Checkbox, Button } from '../ui'
import type { DNSZoneCreate, DNSZoneType } from '../../types'

interface DNSZoneFormProps {
  zoneTypeOptions: DNSZoneType[]
  loading: boolean
  onSubmit: (payload: DNSZoneCreate) => Promise<void>
}

export function DNSZoneForm({ zoneTypeOptions, loading, onSubmit }: DNSZoneFormProps) {
  const [name, setName] = useState('example.internal')
  const [zoneType, setZoneType] = useState<DNSZoneType>(zoneTypeOptions[0])
  const [dnssecEnabled, setDnssecEnabled] = useState(false)

  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault()
        void onSubmit({
          name,
          zone_type: zoneType,
          dnssec_enabled: dnssecEnabled,
        })
      }}
    >
      <Field label="Zone Name">
        <Input
          mono
          value={name}
          onChange={(event) => setName(event.target.value)}
        />
      </Field>
      <Field label="Zone Type">
        <Select
          value={zoneType}
          onChange={(event) => setZoneType(event.target.value as DNSZoneType)}
        >
          {zoneTypeOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </Select>
      </Field>
      <label className="inline-flex items-center gap-2 text-sm cursor-pointer">
        <Checkbox
          checked={dnssecEnabled}
          onChange={(event) => setDnssecEnabled(event.target.checked)}
        />
        Enable DNSSEC
      </label>
      <div className="flex justify-end">
        <Button type="submit" disabled={loading}>
          {loading ? 'Creating…' : 'Create Zone'}
        </Button>
      </div>
    </form>
  )
}
