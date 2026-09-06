import { useState } from 'react'
import { Field, Input, Checkbox, Button } from '../ui'
import type { DNSServerCreate } from '../../types'

interface DNSServerFormProps {
  loading: boolean
  onSubmit: (payload: DNSServerCreate) => Promise<void>
}

export function DNSServerForm({ loading, onSubmit }: DNSServerFormProps) {
  const [name, setName] = useState('dns-server-1')
  const [isRecursive, setIsRecursive] = useState(true)
  const [isAuthoritative, setIsAuthoritative] = useState(true)
  const [forwarders, setForwarders] = useState('1.1.1.1,8.8.8.8')

  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault()
        void onSubmit({
          name,
          is_recursive: isRecursive,
          is_authoritative: isAuthoritative,
          forwarders: forwarders
            .split(',')
            .map((item) => item.trim())
            .filter(Boolean),
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
      <Field label="Forwarders (comma separated)" helper="IP addresses of upstream forwarders">
        <Input
          mono
          value={forwarders}
          onChange={(event) => setForwarders(event.target.value)}
        />
      </Field>
      <div className="flex items-center gap-6 text-sm">
        <label className="inline-flex items-center gap-2 cursor-pointer">
          <Checkbox
            checked={isRecursive}
            onChange={(event) => setIsRecursive(event.target.checked)}
          />
          Recursive
        </label>
        <label className="inline-flex items-center gap-2 cursor-pointer">
          <Checkbox
            checked={isAuthoritative}
            onChange={(event) => setIsAuthoritative(event.target.checked)}
          />
          Authoritative
        </label>
      </div>
      <div className="flex justify-end">
        <Button type="submit" disabled={loading}>
          {loading ? 'Creating…' : 'Create Server'}
        </Button>
      </div>
    </form>
  )
}
