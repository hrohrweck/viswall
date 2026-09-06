import { useState } from 'react'
import { Field, Input, Button } from '../ui'

interface MailboxFormProps {
  domain: string
  loading?: boolean
  onSubmit: (values: { username: string; full_name?: string; password?: string }) => void
  onCancel: () => void
}

export function MailboxForm({ domain, loading, onSubmit, onCancel }: MailboxFormProps) {
  const [username, setUsername] = useState('')
  const [fullName, setFullName] = useState('')
  const [password, setPassword] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!username) return
    onSubmit({
      username,
      full_name: fullName || undefined,
      password: password || undefined,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Field label="Username" required>
        <div className="flex">
          <Input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="user"
            className="rounded-r-none"
            aria-label="Username"
          />
          <span className="inline-flex items-center px-3 rounded-r-card border border-l-0 border-border bg-surface-elevated text-sm text-on-surface-muted">
            @{domain}
          </span>
        </div>
      </Field>
      <Field label="Full Name">
        <Input
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
        />
      </Field>
      <Field label="Password" helper="Leave empty to auto-generate">
        <Input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Auto-generate"
        />
      </Field>
      <div className="flex justify-end gap-3 pt-2">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={!username || loading}>
          {loading ? 'Creating...' : 'Create'}
        </Button>
      </div>
    </form>
  )
}
