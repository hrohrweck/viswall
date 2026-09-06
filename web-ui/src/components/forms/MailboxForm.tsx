import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Field, Input, Button } from '../ui'

interface MailboxFormProps {
  domain: string
  loading?: boolean
  onSubmit: (values: { username: string; full_name?: string; password?: string }) => void
  onCancel: () => void
}

const schema = z.object({
  username: z
    .string()
    .trim()
    .min(1, 'Username is required')
    .refine(
      (value) => !value.includes('@') && !/\s/.test(value),
      'Enter the local part only (without @domain)',
    ),
  full_name: z.string(),
  password: z.string(),
})

type FormValues = z.infer<typeof schema>

export function MailboxForm({ domain, loading, onSubmit, onCancel }: MailboxFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      username: '',
      full_name: '',
      password: '',
    },
  })

  const onValid = (values: FormValues) => {
    onSubmit({
      username: values.username,
      full_name: values.full_name || undefined,
      password: values.password || undefined,
    })
  }

  return (
    <form onSubmit={handleSubmit(onValid)} noValidate className="space-y-4">
      <Field label="Username" required error={errors.username?.message}>
        <div className="flex">
          <Input
            placeholder="user"
            className="rounded-r-none"
            aria-label="Username"
            {...register('username')}
          />
          <span className="inline-flex items-center px-3 rounded-r-card border border-l-0 border-border bg-surface-elevated text-sm text-on-surface-muted">
            @{domain}
          </span>
        </div>
      </Field>
      <Field label="Full Name">
        <Input {...register('full_name')} />
      </Field>
      <Field label="Password" helper="Leave empty to auto-generate">
        <Input type="password" placeholder="Auto-generate" {...register('password')} />
      </Field>
      <div className="flex justify-end gap-3 pt-2">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={loading}>
          {loading ? 'Creating...' : 'Create'}
        </Button>
      </div>
    </form>
  )
}
