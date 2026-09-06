import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button, Checkbox, Field, Input, Select } from '../ui'
import { anyIpOrCidr, hostname } from '../../lib/validation'
import { DHCPHAMode } from '../../types'
import type { DHCPServerCreate } from '../../types'

interface DHCPServerFormProps {
  loading: boolean
  onSubmit: (payload: DHCPServerCreate) => void
}

const schema = z
  .object({
    name: hostname,
    dhcpv4_enabled: z.boolean(),
    dhcpv6_enabled: z.boolean(),
    ha_enabled: z.boolean(),
    ha_mode: z.nativeEnum(DHCPHAMode),
    ha_peer_address: z.string(),
  })
  .superRefine((data, ctx) => {
    if (data.ha_enabled && !anyIpOrCidr.safeParse(data.ha_peer_address).success) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['ha_peer_address'],
        message: 'Enter a valid peer IP address',
      })
    }
  })

type FormValues = z.infer<typeof schema>

export function DHCPServerForm({ loading, onSubmit }: DHCPServerFormProps) {
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: 'kea-dhcp-1',
      dhcpv4_enabled: true,
      dhcpv6_enabled: false,
      ha_enabled: false,
      ha_mode: DHCPHAMode.HOT_STANDBY,
      ha_peer_address: '',
    },
  })

  const haEnabled = watch('ha_enabled')

  const onValid = (values: FormValues) => {
    onSubmit({
      name: values.name,
      dhcpv4_enabled: values.dhcpv4_enabled,
      dhcpv6_enabled: values.dhcpv6_enabled,
      ha_enabled: values.ha_enabled,
      ha_mode: values.ha_mode,
      ha_peer_address: values.ha_enabled ? values.ha_peer_address : undefined,
    })
  }

  return (
    <form onSubmit={handleSubmit(onValid)} noValidate className="space-y-4">
      <Field label="Name" required error={errors.name?.message}>
        <Input {...register('name')} />
      </Field>

      <div className="flex items-center gap-6">
        <label className="inline-flex items-center gap-2 text-sm cursor-pointer">
          <Checkbox {...register('dhcpv4_enabled')} />
          DHCPv4
        </label>
        <label className="inline-flex items-center gap-2 text-sm cursor-pointer">
          <Checkbox {...register('dhcpv6_enabled')} />
          DHCPv6
        </label>
      </div>

      <label className="inline-flex items-center gap-2 text-sm cursor-pointer">
        <Checkbox {...register('ha_enabled')} />
        Enable HA
      </label>

      {haEnabled ? (
        <>
          <Field label="HA Mode">
            <Select {...register('ha_mode')}>
              <option value={DHCPHAMode.HOT_STANDBY}>Hot standby</option>
              <option value={DHCPHAMode.LOAD_BALANCING}>Load balancing</option>
            </Select>
          </Field>
          <Field label="HA Peer Address" required error={errors.ha_peer_address?.message}>
            <Input mono placeholder="10.0.0.2" {...register('ha_peer_address')} />
          </Field>
        </>
      ) : null}

      <div className="flex justify-end">
        <Button type="submit" loading={loading}>
          Create Server
        </Button>
      </div>
    </form>
  )
}
