import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Field, Input, Select, Button } from '../ui'
import { hostname, intString } from '../../lib/validation'
import { DNSRecordType } from '../../types'
import type { DNSRecordCreate } from '../../types'

interface DNSRecordFormProps {
  recordTypeOptions: DNSRecordType[]
  loading: boolean
  onSubmit: (payload: DNSRecordCreate) => Promise<void>
}

const schema = z.object({
  name: z.union([z.literal('@'), hostname]),
  record_type: z.nativeEnum(DNSRecordType),
  content: z.string().trim().min(1, 'Content is required'),
  ttl: intString('TTL must be a whole number'),
})

type FormValues = z.infer<typeof schema>

export function DNSRecordForm({ recordTypeOptions, loading, onSubmit }: DNSRecordFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '@',
      record_type: recordTypeOptions[0],
      content: '192.168.1.10',
      ttl: '3600',
    },
  })

  const onValid = (values: FormValues) => {
    void onSubmit({
      name: values.name,
      record_type: values.record_type,
      content: values.content,
      ttl: Number(values.ttl),
    })
  }

  return (
    <form onSubmit={handleSubmit(onValid)} noValidate className="space-y-4">
      <Field label="Name" required error={errors.name?.message}>
        <Input mono {...register('name')} />
      </Field>
      <Field label="Type">
        <Select {...register('record_type')}>
          {recordTypeOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </Select>
      </Field>
      <Field label="Content" required error={errors.content?.message}>
        <Input mono {...register('content')} />
      </Field>
      <Field label="TTL" error={errors.ttl?.message}>
        <Input type="number" {...register('ttl')} />
      </Field>
      <div className="flex justify-end">
        <Button type="submit" disabled={loading}>
          {loading ? 'Creating…' : 'Create Record'}
        </Button>
      </div>
    </form>
  )
}
