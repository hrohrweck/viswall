import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Field, Input, Select, Checkbox, Button } from '../ui'
import { domainName } from '../../lib/validation'
import { DNSZoneType } from '../../types'
import type { DNSZoneCreate } from '../../types'

interface DNSZoneFormProps {
  zoneTypeOptions: DNSZoneType[]
  loading: boolean
  onSubmit: (payload: DNSZoneCreate) => Promise<void>
}

const schema = z.object({
  name: domainName,
  zone_type: z.nativeEnum(DNSZoneType),
  dnssec_enabled: z.boolean(),
})

type FormValues = z.infer<typeof schema>

export function DNSZoneForm({ zoneTypeOptions, loading, onSubmit }: DNSZoneFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: 'example.internal',
      zone_type: zoneTypeOptions[0],
      dnssec_enabled: false,
    },
  })

  const onValid = (values: FormValues) => {
    void onSubmit({
      name: values.name,
      zone_type: values.zone_type,
      dnssec_enabled: values.dnssec_enabled,
    })
  }

  return (
    <form onSubmit={handleSubmit(onValid)} noValidate className="space-y-4">
      <Field label="Zone Name" required error={errors.name?.message}>
        <Input mono {...register('name')} />
      </Field>
      <Field label="Zone Type">
        <Select {...register('zone_type')}>
          {zoneTypeOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </Select>
      </Field>
      <label htmlFor="dns-zone-dnssec" className="inline-flex items-center gap-2 text-sm cursor-pointer">
        <Checkbox id="dns-zone-dnssec" {...register('dnssec_enabled')} />
        Enable DNSSEC
      </label>
      <div className="flex justify-end">
        <Button type="submit" disabled={loading}>
          {loading ? 'Creating…' : 'Create Zone'}
        </Button>
      </div>
    </form>
  )
}
