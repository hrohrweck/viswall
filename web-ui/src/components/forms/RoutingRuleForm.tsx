import { Controller, useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Field, Input, Switch, Button } from '../ui'
import { anyIpOrCidr, intString, nonEmptyName } from '../../lib/validation'
import type { RoutingRule, RoutingRuleCreate, RoutingRuleUpdate } from '../../types'

interface RoutingRuleFormProps {
  initial?: RoutingRule
  onSubmit: (data: RoutingRuleCreate | RoutingRuleUpdate) => void
  onCancel: () => void
  loading: boolean
}

const optionalCidr = (message: string) =>
  z.string().refine((value) => value === '' || anyIpOrCidr.safeParse(value).success, message)

const schema = z.object({
  name: nonEmptyName,
  enabled: z.boolean(),
  source_network: optionalCidr('Enter a valid network CIDR (e.g. 10.0.0.0/24)'),
  dest_network: optionalCidr('Enter a valid network CIDR (e.g. 0.0.0.0/0)'),
  service: z.string(),
  inbound_interface: z.string(),
  gateway: optionalCidr('Enter a valid gateway IP address'),
  outbound_interface: z.string(),
  mark: z.string().refine(
    (value) => value === '' || intString().safeParse(value).success,
    'Enter a whole number',
  ),
})

type FormValues = z.infer<typeof schema>

export function RoutingRuleForm({ initial, onSubmit, onCancel, loading }: RoutingRuleFormProps) {
  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: initial?.name || '',
      enabled: initial?.enabled ?? true,
      source_network: initial?.source_network || '',
      dest_network: initial?.dest_network || '',
      service: initial?.service || '',
      inbound_interface: initial?.inbound_interface || '',
      gateway: initial?.gateway || '',
      outbound_interface: initial?.outbound_interface || '',
      mark: initial?.mark?.toString() || '',
    },
  })

  const onValid = (values: FormValues) => {
    const payload: RoutingRuleCreate = {
      name: values.name,
      enabled: values.enabled,
      source_network: values.source_network || undefined,
      dest_network: values.dest_network || undefined,
      service: values.service || undefined,
      inbound_interface: values.inbound_interface || undefined,
      gateway: values.gateway || undefined,
      outbound_interface: values.outbound_interface || undefined,
      mark: values.mark ? parseInt(values.mark, 10) : undefined,
      order_index: initial?.order_index,
    }
    onSubmit(payload)
  }

  return (
    <form onSubmit={handleSubmit(onValid)} noValidate className="space-y-4">
      <Field label="Name" required error={errors.name?.message}>
        <Input type="text" placeholder="e.g. Route DMZ to WAN" {...register('name')} />
      </Field>

      <div className="flex items-center gap-2">
        <Controller
          name="enabled"
          control={control}
          render={({ field }) => (
            <Switch checked={field.value} onCheckedChange={field.onChange} aria-label="Enabled" />
          )}
        />
        <span className="text-sm text-on-surface">Enabled</span>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Field label="Source Network" error={errors.source_network?.message}>
          <Input type="text" mono placeholder="10.0.0.0/24" {...register('source_network')} />
        </Field>
        <Field label="Dest Network" error={errors.dest_network?.message}>
          <Input type="text" mono placeholder="0.0.0.0/0" {...register('dest_network')} />
        </Field>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Field label="Service">
          <Input type="text" placeholder="tcp/80" {...register('service')} />
        </Field>
        <Field label="Inbound Interface">
          <Input type="text" placeholder="eth0" {...register('inbound_interface')} />
        </Field>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Field label="Gateway" error={errors.gateway?.message}>
          <Input type="text" mono placeholder="192.168.1.1" {...register('gateway')} />
        </Field>
        <Field label="Outbound Interface">
          <Input type="text" placeholder="eth1" {...register('outbound_interface')} />
        </Field>
      </div>

      <Field label="Firewall Mark (fwmark)" error={errors.mark?.message}>
        <Input type="number" placeholder="100" {...register('mark')} />
      </Field>

      <div className="flex items-center justify-end gap-2 pt-4">
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
