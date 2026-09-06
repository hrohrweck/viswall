import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button, Field, Input } from '../ui'
import { cn } from '../../lib/utils'
import { hostname, nonEmptyName } from '../../lib/validation'
import type { InstanceCreate } from '../../types'

interface InstanceCreateFormProps {
  onSubmit: (data: InstanceCreate) => Promise<void>
  onCancel: () => void
  loading: boolean
}

const schema = z.object({
  name: nonEmptyName,
  hostname: hostname,
  capabilities: z.array(z.string()),
})

type FormValues = z.infer<typeof schema>

const CAPABILITIES = ['firewall', 'mail', 'vpn', 'metrics']

export function InstanceCreateForm({ onSubmit, onCancel, loading }: InstanceCreateFormProps) {
  const [submitError, setSubmitError] = useState('')
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '',
      hostname: '',
      capabilities: [],
    },
  })

  const selectedCaps = watch('capabilities')

  const toggleCap = (cap: string) => {
    setValue(
      'capabilities',
      selectedCaps.includes(cap) ? selectedCaps.filter((c) => c !== cap) : [...selectedCaps, cap],
      { shouldValidate: true },
    )
  }

  const onValid = async (values: FormValues): Promise<void> => {
    setSubmitError('')
    try {
      await onSubmit({ name: values.name, hostname: values.hostname, capabilities: values.capabilities })
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setSubmitError(detail || 'Failed to create instance')
    }
  }

  return (
    <form onSubmit={handleSubmit(onValid)} noValidate className="space-y-4">
      {submitError && (
        <div className="p-3 rounded-card border border-danger bg-danger-subtle text-danger text-sm">
          {submitError}
        </div>
      )}

      <Field label="Name" required error={errors.name?.message}>
        <Input type="text" placeholder="e.g. Main Office" {...register('name')} />
      </Field>

      <Field label="Hostname" required error={errors.hostname?.message}>
        <Input type="text" mono placeholder="e.g. viswall.example.com" {...register('hostname')} />
      </Field>

      <div>
        <span className="block text-sm font-medium text-on-surface mb-2">Capabilities</span>
        <div className="flex flex-wrap gap-2">
          {CAPABILITIES.map((cap) => (
            <button
              key={cap}
              type="button"
              onClick={() => toggleCap(cap)}
              aria-pressed={selectedCaps.includes(cap)}
              className={cn(
                'px-3 py-1.5 rounded-card text-sm font-medium border transition-colors',
                selectedCaps.includes(cap)
                  ? 'bg-primary-subtle border-primary text-primary'
                  : 'bg-surface-card border-border text-on-surface-muted hover:bg-surface-elevated',
              )}
            >
              {cap}
            </button>
          ))}
        </div>
      </div>

      <div className="flex justify-end gap-3 pt-4">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" loading={loading}>
          {loading ? 'Creating...' : 'Create Instance'}
        </Button>
      </div>
    </form>
  )
}
