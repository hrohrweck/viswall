import { useMemo } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button, Field, Input } from '../ui'
import { ipv4OrCidr, ipv6OrCidr } from '../../lib/validation'
import { DHCPSubnetType } from '../../types'
import type { DHCPPoolCreate } from '../../types'

interface DHCPPoolFormProps {
  subnetType: DHCPSubnetType
  loading: boolean
  onSubmit: (payload: DHCPPoolCreate) => void
}

const makeSchema = (subnetType: DHCPSubnetType) => {
  const address = subnetType === DHCPSubnetType.V4 ? ipv4OrCidr : ipv6OrCidr
  return z.object({
    start_address: address,
    end_address: address,
  })
}

type FormValues = {
  start_address: string
  end_address: string
}

export function DHCPPoolForm({ subnetType, loading, onSubmit }: DHCPPoolFormProps) {
  const schema = useMemo(() => makeSchema(subnetType), [subnetType])
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      start_address: subnetType === DHCPSubnetType.V4 ? '192.168.10.100' : '2001:db8::100',
      end_address: subnetType === DHCPSubnetType.V4 ? '192.168.10.200' : '2001:db8::1ff',
    },
  })

  const onValid = (values: FormValues) => {
    onSubmit({ start_address: values.start_address, end_address: values.end_address, type: subnetType })
  }

  return (
    <form onSubmit={handleSubmit(onValid)} noValidate className="space-y-4">
      <Field label="Start Address" required error={errors.start_address?.message}>
        <Input mono {...register('start_address')} />
      </Field>
      <Field label="End Address" required error={errors.end_address?.message}>
        <Input mono {...register('end_address')} />
      </Field>
      <div className="flex justify-end">
        <Button type="submit" loading={loading}>
          Create Pool
        </Button>
      </div>
    </form>
  )
}
