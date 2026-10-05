import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Plus, Trash2 } from 'lucide-react'
import { Field, Input, Button, Switch } from '../ui'

interface MailAliasFormProps {
  domain: string
  mode: 'create' | 'edit'
  initial?: { source: string; destinations: string[]; enabled: boolean }
  loading?: boolean
  onSubmit: (values: { source: string; destinations: string[]; enabled: boolean }) => void
  onCancel: () => void
}

const schema = z.object({
  source: z
    .string()
    .trim()
    .min(1, 'Source is required')
    .refine(
      (value) => value === '*' || (!value.includes('@') && !/\s/.test(value)),
      'Use a local part (without @domain) or "*" for catch-all',
    ),
  destinations: z
    .array(
      z
        .string()
        .trim()
        .min(1, 'Destination is required')
        .email('Enter a valid email address'),
    )
    .min(1, 'At least one destination'),
  enabled: z.boolean(),
})

type FormValues = z.infer<typeof schema>

export function MailAliasForm({ domain, mode, initial, loading, onSubmit, onCancel }: MailAliasFormProps) {
  const isEdit = mode === 'edit'
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      source: initial?.source ?? '',
      destinations: initial?.destinations ?? [''],
      enabled: initial?.enabled ?? true,
    },
  })
  const source = watch('source')
  const enabled = watch('enabled')
  const destinations = watch('destinations')

  const preview = source === '*' || !source ? `@${domain}` : `${source}@${domain}`
  const destinationsError = errors.destinations?.root?.message ?? errors.destinations?.message

  const addDestination = () => setValue('destinations', [...destinations, ''], { shouldDirty: true })
  const removeDestination = (index: number) =>
    setValue(
      'destinations',
      destinations.filter((_, i) => i !== index),
      { shouldDirty: true },
    )

  const onValid = (values: FormValues) => {
    onSubmit({
      source: values.source,
      destinations: values.destinations,
      enabled: values.enabled,
    })
  }

  return (
    <form onSubmit={handleSubmit(onValid)} noValidate className="space-y-4">
      <Field
        label="Source"
        required
        error={errors.source?.message}
        helper={isEdit ? 'The source address cannot be changed — edit destinations only.' : undefined}
      >
        <div className="flex">
          <Input
            placeholder="team"
            className="rounded-r-none disabled:opacity-60"
            aria-label="Source"
            disabled={isEdit}
            {...register('source')}
          />
          <span className="inline-flex items-center px-3 rounded-r-card border border-l-0 border-border bg-surface-elevated text-sm text-on-surface-muted font-mono">
            {preview}
          </span>
        </div>
      </Field>

      <Field label="Destinations" required error={destinationsError}>
        <div className="space-y-2">
          {destinations.map((destination, index) => (
            <div key={index} className="space-y-1">
              <div className="flex gap-2">
                <Input
                  placeholder="user@example.com"
                  aria-label={`Destination ${index + 1}`}
                  aria-invalid={!!errors.destinations?.[index]?.message || undefined}
                  {...register(`destinations.${index}`)}
                />
                <button
                  type="button"
                  aria-label={`Remove destination ${index + 1}`}
                  onClick={() => removeDestination(index)}
                  disabled={destinations.length === 1}
                  className="inline-flex items-center justify-center w-9 h-9 rounded-lg border border-border text-on-surface-muted hover:text-danger hover:border-danger/50 hover:bg-danger-subtle transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
              {errors.destinations?.[index]?.message && (
                <p role="alert" className="flex items-center gap-1 text-xs text-danger">
                  {errors.destinations[index]?.message}
                </p>
              )}
            </div>
          ))}
          <Button type="button" variant="secondary" size="sm" onClick={addDestination}>
            <Plus className="w-4 h-4" />
            Add destination
          </Button>
        </div>
      </Field>

      <div className="flex items-center justify-between pt-1">
        <div>
          <p className="text-sm font-medium text-on-surface">Enabled</p>
          <p className="text-xs text-on-surface-muted">Deliver to this alias when active.</p>
        </div>
        <Switch
          checked={enabled}
          onCheckedChange={(checked) => setValue('enabled', checked, { shouldDirty: true })}
          aria-label="Enabled"
        />
      </div>

      <div className="flex justify-end gap-3 pt-2">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={loading}>
          {loading ? 'Saving...' : isEdit ? 'Save Changes' : 'Create Alias'}
        </Button>
      </div>
    </form>
  )
}
