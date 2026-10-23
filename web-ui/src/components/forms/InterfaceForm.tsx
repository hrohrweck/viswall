import { Controller, useFieldArray, useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Plus, Trash2 } from 'lucide-react'
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

const ipv6Address = z
  .string()
  .refine((value) => value === '' || value.includes(':'), 'Enter a valid IPv6 address, e.g. 2001:db8::1/64')

const netmask = z
  .string()
  .refine(
    (value) =>
      value === '' ||
      /^(255|254|252|248|240|224|192|128|0)\.(255|254|252|248|240|224|192|128|0)\.(255|254|252|248|240|224|192|128|0)\.(255|254|252|248|240|224|192|128|0)$/.test(value),
    'Use dotted-decimal form, e.g. 255.255.255.0',
  )

const routeTo = z
  .string()
  .refine((value) => value !== '' && /^[0-9A-Fa-f:.]+(\/\d{1,3})?$/.test(value), 'Enter a CIDR, e.g. 10.80.0.0/16')

const makeSchema = (isEdit: boolean) =>
  z
    .object({
      name: ifaceName,
      type: z.enum(['wan', 'lan', 'dmz', 'other']),
      config_type: z.enum(['dhcp', 'static']),
      ip_address: ipAddress,
      netmask,
      gateway: ipAddress,
      ipv6_address: ipv6Address,
      ipv6_gateway: ipv6Address,
      dns_servers: z.string(),
      routes: z.array(
        z.object({
          to: routeTo,
          via: z.string(),
          on_link: z.boolean(),
        }),
      ),
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
    .superRefine((v, ctx) => {
      v.routes.forEach((route, idx) => {
        if (route.to !== '' && !route.on_link && route.via.trim() === '') {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: 'A route needs a gateway unless it is on-link',
            path: ['routes', idx, 'via'],
          })
        }
      })
    })

type FormValues = z.infer<ReturnType<typeof makeSchema>>

const splitList = (raw: string): string[] =>
  raw
    .split(',')
    .map((entry) => entry.trim())
    .filter((entry) => entry.length > 0)

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
      ipv6_address: initial?.ipv6_address || '',
      ipv6_gateway: initial?.ipv6_gateway || '',
      dns_servers: initial?.dns_servers?.join(', ') || '',
      routes:
        initial?.routes?.map((route) => ({
          to: route.to || '',
          via: route.via || '',
          on_link: route.on_link ?? false,
        })) || [],
      mtu: initial?.mtu?.toString() || '',
      description: initial?.description || '',
      enabled: initial?.enabled ?? true,
    },
  })

  const { fields, append, remove } = useFieldArray({ control, name: 'routes' })

  const configType = watch('config_type')

  const onValid = (values: FormValues) => {
    const common = {
      name: values.name,
      type: values.type,
      config_type: values.config_type,
      ip_address: values.ip_address || null,
      netmask: values.netmask || null,
      gateway: values.gateway || null,
      ipv6_address: values.ipv6_address || null,
      ipv6_gateway: values.ipv6_gateway || null,
      dns_servers: splitList(values.dns_servers),
      routes: values.routes.map((route) => ({
        to: route.to.trim(),
        via: route.via.trim() || null,
        on_link: route.on_link,
      })),
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

      <Field label="IPv6 Address" error={errors.ipv6_address?.message} helper="Optional, e.g. 2001:db8::2/64">
        <Input type="text" placeholder="2001:db8::2/64" {...register('ipv6_address')} />
      </Field>
      <Field label="IPv6 Gateway" error={errors.ipv6_gateway?.message} helper="Optional — sets the IPv6 default route">
        <Input type="text" placeholder="fe80::1" {...register('ipv6_gateway')} />
      </Field>

      <Field
        label="DNS Servers"
        error={errors.dns_servers?.message}
        helper="Optional — comma-separated, e.g. 185.12.64.1, 1.1.1.1"
      >
        <Input type="text" placeholder="1.1.1.1, 8.8.8.8" {...register('dns_servers')} />
      </Field>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-on-surface">Extra Routes</span>
          <Button
            type="button"
            variant="ghost"
            icon={Plus}
            onClick={() => append({ to: '', via: '', on_link: false })}
          >
            Add Route
          </Button>
        </div>
        {fields.length === 0 ? (
          <p className="text-xs text-on-surface-muted">No extra routes — add one to route traffic to a specific network.</p>
        ) : (
          <div className="space-y-2">
            {fields.map((field, idx) => (
              <div key={field.id} className="rounded-md border border-border p-3 space-y-2">
                <div className="grid grid-cols-[1fr_1fr_auto] gap-2 items-start">
                  <Field label={`Destination (${idx + 1})`} required error={errors.routes?.[idx]?.to?.message}>
                    <Input type="text" placeholder="10.80.0.0/16" {...register(`routes.${idx}.to`)} />
                  </Field>
                  <Field label="Gateway" error={errors.routes?.[idx]?.via?.message}>
                    <Input type="text" placeholder="10.80.0.1" {...register(`routes.${idx}.via`)} />
                  </Field>
                  <div className="pt-6">
                    <Button
                      type="button"
                      variant="ghost"
                      icon={Trash2}
                      aria-label={`Remove route ${idx + 1}`}
                      onClick={() => remove(idx)}
                    />
                  </div>
                </div>
                <label className="flex items-center gap-2 text-sm text-on-surface">
                  <input type="checkbox" className="mt-0.5" {...register(`routes.${idx}.on_link`)} />
                  <span>On-link route (no gateway)</span>
                </label>
              </div>
            ))}
          </div>
        )}
      </div>

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
