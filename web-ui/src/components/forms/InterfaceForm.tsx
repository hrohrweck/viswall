import { Controller, useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Field, Input, Select, Switch, Button } from '../ui'
import type { NetworkInterface, NetworkInterfaceCreate, NetworkInterfaceUpdate } from '../../types'

interface InterfaceFormProps {
  initial?: NetworkInterface
  onSubmit: (data: NetworkInterfaceCreate | NetworkInterfaceUpdate) => void
  onCancel: () => void
  loading: boolean
}

const ifaceName = z
  .string()
  .regex(/^[a-zA-Z0-9._-]{1,15}$/, 'Use 1-15 characters: letters, digits, dot, dash, underscore')
  .refine((value) => value !== 'lo', 'The loopback interface cannot be managed')

const ipAddress = z
  .string()
  .refine((value) => value === '' || /^\d{1,3}(\.\d{1,3}){3}$/.test(value), 'Enter a valid IPv4 address')

const netmask = z
  .string()
  .refine(
    (value) =>
      value === '' ||
      /^(255|254|252|248|240|224|192|128|0)\.(255|254|252|248|240|224|192|128|0)\.(255|254|252|248|240|224|192|128|0)\.(255|254|252|248|240|224|192|128|0)$/.test(value),
    'Use dotted-decimal form, e.g. 255.255.255.0',
  )

const makeSchema = (isEdit: boolean) =>
  z
    .object({
      name: ifaceName,
      type: z.enum(['wan', 'lan', 'dmz', 'other']),
      config_type: z.enum(['dhcp', 'static']),
      ip_address: ipAddress,
      netmask,
      gateway: ipAddress,
      mtu: z.string().refine(
        (value) => value === '' || (/^\d+$/.test(value) && Number(value) >= 68 && Number(value) <= 65535),
        'MTU must be 68-65535',
      ),
      description: z.string(),
      enabled: z.boolean(),
    })
    .refine((v) => v.config_type !== 'static' || v.ip_address !== '', {
      message: 'Static configuration requires an IP address',
      path: ['ip_address'],
    })
    .refine((v) => v.config_type !== 'static' || v.netmask !== '', {
      message: 'Static configuration requires a netmask',
      path: ['netmask'],
    })

type FormValues = z.infer<ReturnType<typeof makeSchema>>

export function InterfaceForm({ initial, onSubmit, onCancel, loading }: InterfaceFormProps) {
  const {
    register,
    handleSubmit,
    control,
    watch,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(makeSchema(!!initial)),
    defaultValues: {
      name: initial?.name || '',
      type: (initial?.type as FormValues['type']) || 'other',
      config_type: (initial?.config_type as FormValues['config_type']) || 'dhcp',
      ip_address: initial?.ip_address || '',
      netmask: initial?.netmask || '',
      gateway: initial?.gateway || '',
      mtu: initial?.mtu?.toString() || '',
      description: initial?.description || '',
      enabled: initial?.enabled ?? true,
    },
  })

  const configType = watch('config_type')

  const onValid = (values: FormValues) => {
    const common = {
      name: values.name,
      type: values.type,
      config_type: values.config_type,
      ip_address: values.ip_address || null,
      netmask: values.netmask || null,
      gateway: values.gateway || null,
      mtu: values.mtu === '' ? null : Number(values.mtu),
      description: values.description || null,
      enabled: values.enabled,
    }
    if (initial) {
      onSubmit(common as NetworkInterfaceUpdate)
    } else {
      onSubmit(common as NetworkInterfaceCreate)
    }
  }

  return (
    <form onSubmit={handleSubmit(onValid)} noValidate className="space-y-4">
      <Field label="Interface Name" required error={errors.name?.message} helper="Host interface, e.g. ens18 or eth0">
        <Input type="text" placeholder="ens18" {...register('name')} />
      </Field>

      <div className="grid grid-cols-2 gap-4">
        <Field label="Role">
          <Select {...register('type')}>
            <option value="wan">WAN</option>
            <option value="lan">LAN</option>
            <option value="dmz">DMZ</option>
            <option value="other">Other</option>
          </Select>
        </Field>
        <Field label="Configuration">
          <Select {...register('config_type')}>
            <option value="dhcp">DHCP</option>
            <option value="static">Static</option>
          </Select>
        </Field>
      </div>

      {configType === 'static' && (
        <>
          <Field label="IP Address" required error={errors.ip_address?.message}>
            <Input type="text" placeholder="10.0.0.5" {...register('ip_address')} />
          </Field>
          <Field label="Netmask" required error={errors.netmask?.message}>
            <Input type="text" placeholder="255.255.255.0" {...register('netmask')} />
          </Field>
          <Field label="Gateway" error={errors.gateway?.message} helper="Optional — sets the default route">
            <Input type="text" placeholder="10.0.0.1" {...register('gateway')} />
          </Field>
        </>
      )}

      <div className="grid grid-cols-2 gap-4">
        <Field label="MTU" error={errors.mtu?.message} helper="Optional">
          <Input type="number" placeholder="1500" {...register('mtu')} />
        </Field>
        <Field label="Description">
          <Input type="text" placeholder="Uplink" {...register('description')} />
        </Field>
      </div>

      <div className="flex items-center gap-2">
        <Controller
          name="enabled"
          control={control}
          render={({ field }) => (
            <Switch checked={field.value} onCheckedChange={field.onChange} aria-label="Interface enabled" />
          )}
        />
        <span className="text-sm text-on-surface">Interface enabled</span>
      </div>

      <div className="flex justify-end gap-3 pt-4">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" loading={loading}>
          {initial ? 'Update' : 'Add Interface'}
        </Button>
      </div>
    </form>
  )
}
