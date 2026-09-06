import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button, Field, Input, Select } from '../ui'
import { hostname, intString, ipList, ipv4OrCidr, ipv6OrCidr } from '../../lib/validation'
import { DHCPSubnetType } from '../../types'
import type { DHCPSubnetCreate } from '../../types'

interface DHCPSubnetFormProps {
  loading: boolean
  onSubmit: (payload: DHCPSubnetCreate) => void
}

const schema = z
  .object({
    name: hostname,
    subnet: z.string(),
    type: z.nativeEnum(DHCPSubnetType),
    routers: ipList,
    dns_servers: ipList,
    lease_time_min: intString('Lease time must be a whole number'),
    lease_time_default: intString('Lease time must be a whole number'),
    lease_time_max: intString('Lease time must be a whole number'),
    delegated_prefix_length: z.string().refine(
      (value) =>
        value === '' ||
        (intString().safeParse(value).success && Number(value) <= 128),
      'Prefix length must be a whole number between 0 and 128',
    ),
  })
  .superRefine((data, ctx) => {
    const cidr = data.type === DHCPSubnetType.V4 ? ipv4OrCidr : ipv6OrCidr
    if (!cidr.safeParse(data.subnet).success) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['subnet'],
        message:
          data.type === DHCPSubnetType.V4
            ? 'Enter a valid IPv4 subnet CIDR (e.g. 192.168.10.0/24)'
            : 'Enter a valid IPv6 subnet CIDR (e.g. fd00::/64)',
      })
    }
  })

type FormValues = z.infer<typeof schema>

export function DHCPSubnetForm({ loading, onSubmit }: DHCPSubnetFormProps) {
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: 'lan-subnet',
      subnet: '192.168.10.0/24',
      type: DHCPSubnetType.V4,
      routers: '192.168.10.1',
      dns_servers: '192.168.10.53',
      lease_time_min: '300',
      lease_time_default: '3600',
      lease_time_max: '7200',
      delegated_prefix_length: '',
    },
  })

  const subnetType = watch('type')

  const onValid = (values: FormValues) => {
    onSubmit({
      name: values.name,
      subnet: values.subnet,
      type: values.type,
      routers: values.routers.split(',').map((item) => item.trim()).filter(Boolean),
      dns_servers: values.dns_servers.split(',').map((item) => item.trim()).filter(Boolean),
      lease_time_min: Number(values.lease_time_min),
      lease_time_default: Number(values.lease_time_default),
      lease_time_max: Number(values.lease_time_max),
      delegated_prefix_length: values.delegated_prefix_length
        ? Number(values.delegated_prefix_length)
        : undefined,
    })
  }

  return (
    <form onSubmit={handleSubmit(onValid)} noValidate className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Field label="Name" required error={errors.name?.message}>
          <Input {...register('name')} />
        </Field>
        <Field label="Type">
          <Select {...register('type')}>
            <option value={DHCPSubnetType.V4}>IPv4</option>
            <option value={DHCPSubnetType.V6}>IPv6</option>
          </Select>
        </Field>
      </div>

      <Field label="Subnet CIDR" required error={errors.subnet?.message}>
        <Input mono {...register('subnet')} />
      </Field>

      <Field label="Routers (comma separated)" error={errors.routers?.message}>
        <Input mono {...register('routers')} />
      </Field>

      <Field label="DNS servers (comma separated)" error={errors.dns_servers?.message}>
        <Input mono {...register('dns_servers')} />
      </Field>

      <div className="grid grid-cols-3 gap-3">
        <Field label="Min" error={errors.lease_time_min?.message}>
          <Input type="number" {...register('lease_time_min')} />
        </Field>
        <Field label="Default" error={errors.lease_time_default?.message}>
          <Input type="number" {...register('lease_time_default')} />
        </Field>
        <Field label="Max" error={errors.lease_time_max?.message}>
          <Input type="number" {...register('lease_time_max')} />
        </Field>
      </div>

      {subnetType === DHCPSubnetType.V6 ? (
        <Field
          label="Delegated Prefix Length (optional)"
          error={errors.delegated_prefix_length?.message}
        >
          <Input placeholder="64" {...register('delegated_prefix_length')} />
        </Field>
      ) : null}

      <div className="flex justify-end">
        <Button type="submit" loading={loading}>
          Create Subnet
        </Button>
      </div>
    </form>
  )
}
