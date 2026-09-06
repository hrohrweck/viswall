import { useMemo } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button, Field, Input } from '../ui'
import { hostname, ipv4OrCidr, ipv6OrCidr, macAddress } from '../../lib/validation'
import { DHCPSubnetType } from '../../types'
import type { DHCPReservationCreate } from '../../types'

interface DHCPReservationFormProps {
  subnetType: DHCPSubnetType
  loading: boolean
  onSubmit: (payload: DHCPReservationCreate) => void
}

const makeSchema = (subnetType: DHCPSubnetType) => {
  const address = subnetType === DHCPSubnetType.V4 ? ipv4OrCidr : ipv6OrCidr
  return z.object({
    hostname: hostname,
    ip_address: address,
    hw_address: macAddress,
  })
}

type FormValues = {
  hostname: string
  ip_address: string
  hw_address: string
}

export function DHCPReservationForm({
  subnetType,
  loading,
  onSubmit,
}: DHCPReservationFormProps) {
  const schema = useMemo(() => makeSchema(subnetType), [subnetType])
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      hostname: 'host-01',
      ip_address: subnetType === DHCPSubnetType.V4 ? '192.168.10.10' : '2001:db8::10',
      hw_address:
        subnetType === DHCPSubnetType.V4
          ? '52:54:00:12:34:56'
          : '00:03:00:01:52:54:00:12:34:56',
    },
  })

  const onValid = (values: FormValues) => {
    onSubmit({
      hostname: values.hostname,
      ip_address: values.ip_address,
      hw_address: values.hw_address,
      type: subnetType,
    })
  }

  return (
    <form onSubmit={handleSubmit(onValid)} noValidate className="space-y-4">
      <Field label="Hostname" required error={errors.hostname?.message}>
        <Input {...register('hostname')} />
      </Field>
      <Field label="IP Address" required error={errors.ip_address?.message}>
        <Input mono {...register('ip_address')} />
      </Field>
      <Field
        label={subnetType === DHCPSubnetType.V4 ? 'MAC Address' : 'DUID'}
        required
        error={errors.hw_address?.message}
      >
        <Input mono {...register('hw_address')} />
      </Field>
      <div className="flex justify-end">
        <Button type="submit" loading={loading}>
          Create Reservation
        </Button>
      </div>
    </form>
  )
}
