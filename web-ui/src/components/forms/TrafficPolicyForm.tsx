import { Controller, useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Field, Input, Select, Switch, Button } from '../ui'
import { nonEmptyName } from '../../lib/validation'
import type { QoSPolicy, QoSPolicyCreate, QoSPolicyUpdate } from '../../types'

interface TrafficPolicyFormProps {
  initial?: QoSPolicy
  onSubmit: (data: QoSPolicyCreate | QoSPolicyUpdate) => void
  onCancel: () => void
  loading: boolean
}

const bandwidth = z.string().refine(
  (value) => /^\d+$/.test(value) && Number(value) >= 1,
  'Enter a bandwidth in Kbps (whole number, minimum 1)',
)

const makeSchema = (isEdit: boolean) =>
  z.object({
    name: nonEmptyName,
    description: z.string(),
    interface_name: z.string().refine(
      (value) => isEdit || value.trim() !== '',
      'Interface is required',
    ),
    algorithm: z.enum(['cake', 'fq_codel', 'htb']),
    download_kbps: bandwidth,
    upload_kbps: bandwidth,
    enabled: z.boolean(),
  })

type FormValues = z.infer<ReturnType<typeof makeSchema>>

export function TrafficPolicyForm({ initial, onSubmit, onCancel, loading }: TrafficPolicyFormProps) {
  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(makeSchema(!!initial)),
    defaultValues: {
      name: initial?.name || '',
      description: initial?.description || '',
      interface_name: initial?.interface_name || 'eth0',
      algorithm: (initial?.algorithm as 'cake' | 'fq_codel' | 'htb') || 'cake',
      download_kbps: initial?.download_kbps?.toString() || '100000',
      upload_kbps: initial?.upload_kbps?.toString() || '50000',
      enabled: initial?.enabled ?? true,
    },
  })

  const onValid = (values: FormValues) => {
    if (initial) {
      const payload: QoSPolicyUpdate = {
        name: values.name,
        description: values.description || undefined,
        enabled: values.enabled,
        algorithm: values.algorithm,
        download_kbps: Number(values.download_kbps),
        upload_kbps: Number(values.upload_kbps),
      }
      onSubmit(payload)
    } else {
      const payload: QoSPolicyCreate = {
        name: values.name,
        description: values.description || undefined,
        interface_name: values.interface_name,
        algorithm: values.algorithm,
        download_kbps: Number(values.download_kbps),
        upload_kbps: Number(values.upload_kbps),
        enabled: values.enabled,
        classes: [],
      }
      onSubmit(payload)
    }
  }

  return (
    <form onSubmit={handleSubmit(onValid)} noValidate className="space-y-4">
      <Field label="Policy Name" required error={errors.name?.message}>
        <Input type="text" {...register('name')} />
      </Field>

      <Field label="Description">
        <Input type="text" {...register('description')} />
      </Field>

      <Field label="Interface" required error={errors.interface_name?.message}>
        <Input type="text" disabled={!!initial} {...register('interface_name')} />
      </Field>

      <Field label="Algorithm">
        <Select {...register('algorithm')}>
          <option value="cake">CAKE (Recommended)</option>
          <option value="fq_codel">FQ-CoDel</option>
          <option value="htb">HTB (Advanced)</option>
        </Select>
      </Field>

      <div className="grid grid-cols-2 gap-4">
        <Field label="Download (Kbps)" required error={errors.download_kbps?.message}>
          <Input type="number" {...register('download_kbps')} />
        </Field>
        <Field label="Upload (Kbps)" required error={errors.upload_kbps?.message}>
          <Input type="number" {...register('upload_kbps')} />
        </Field>
      </div>

      <div className="flex items-center gap-2">
        <Controller
          name="enabled"
          control={control}
          render={({ field }) => (
            <Switch checked={field.value} onCheckedChange={field.onChange} aria-label="Enable policy immediately" />
          )}
        />
        <span className="text-sm text-on-surface">Enable policy immediately</span>
      </div>

      <div className="flex justify-end gap-3 pt-4">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" loading={loading}>
          {initial ? 'Update' : 'Create'}
        </Button>
      </div>
    </form>
  )
}
