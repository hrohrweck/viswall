import { useState } from 'react'
import { Field, Input, Select, Button } from '../ui'
import type { DNSRecordCreate, DNSRecordType } from '../../types'

interface DNSRecordFormProps {
  recordTypeOptions: DNSRecordType[]
  loading: boolean
  onSubmit: (payload: DNSRecordCreate) => Promise<void>
}

export function DNSRecordForm({ recordTypeOptions, loading, onSubmit }: DNSRecordFormProps) {
  const [name, setName] = useState('@')
  const [recordType, setRecordType] = useState<DNSRecordType>(recordTypeOptions[0])
  const [content, setContent] = useState('192.168.1.10')
  const [ttl, setTtl] = useState(3600)

  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault()
        void onSubmit({
          name,
          record_type: recordType,
          content,
          ttl,
        })
      }}
    >
      <Field label="Name">
        <Input
          mono
          value={name}
          onChange={(event) => setName(event.target.value)}
        />
      </Field>
      <Field label="Type">
        <Select
          value={recordType}
          onChange={(event) => setRecordType(event.target.value as DNSRecordType)}
        >
          {recordTypeOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </Select>
      </Field>
      <Field label="Content">
        <Input
          mono
          value={content}
          onChange={(event) => setContent(event.target.value)}
        />
      </Field>
      <Field label="TTL">
        <Input
          type="number"
          min={0}
          value={ttl}
          onChange={(event) => setTtl(Number(event.target.value))}
        />
      </Field>
      <div className="flex justify-end">
        <Button type="submit" disabled={loading}>
          {loading ? 'Creating…' : 'Create Record'}
        </Button>
      </div>
    </form>
  )
}
