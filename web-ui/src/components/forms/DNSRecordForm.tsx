import { useMemo } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Field, Input, Select, Button } from '../ui'
import { dnsRecordName, intString } from '../../lib/validation'
import { DNSRecordType } from '../../types'
import type { DNSRecord, DNSRecordCreate, DNSRecordUpdate } from '../../types'

interface DNSRecordFormProps {
  recordTypeOptions: DNSRecordType[]
  loading: boolean
  onSubmit: (payload: DNSRecordCreate | DNSRecordUpdate) => Promise<void>
  /** Zone the record is created in — enables the full-FQDN-relative guard. */
  zoneName?: string
  /** Existing record — switches the form into edit mode. */
  initial?: DNSRecord
  onCancel?: () => void
}

const makeSchema = (zoneName?: string) =>
  z
    .object({
      name: dnsRecordName,
      record_type: z.nativeEnum(DNSRecordType),
      content: z.string().trim().min(1, 'Content is required'),
      ttl: intString('TTL must be a whole number'),
    })
    .superRefine((values, ctx) => {
      if (!zoneName || values.name === '@' || values.name.endsWith('.')) return
      const zone = zoneName.toLowerCase()
      if (values.name.toLowerCase() === zone || values.name.toLowerCase().endsWith('.' + zone)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ['name'],
          message: `Enter the record relative to the zone (e.g. mail._domainkey), use @ for the zone apex, or add a trailing dot for the absolute name — remove ".${zoneName}"`,
        })
      }
    })

type FormValues = z.infer<ReturnType<typeof makeSchema>>

export function DNSRecordForm({ recordTypeOptions, loading, onSubmit, zoneName, initial, onCancel }: DNSRecordFormProps) {
  const schema = useMemo(() => makeSchema(zoneName), [zoneName])
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: initial?.name || '@',
      record_type: initial?.record_type || recordTypeOptions[0],
      content: initial?.content || '192.168.1.10',
      ttl: initial ? String(initial.ttl) : '3600',
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
      <div className="flex justify-end gap-3">
        {onCancel && (
          <Button type="button" variant="secondary" onClick={onCancel}>
            Cancel
          </Button>
        )}
        <Button type="submit" disabled={loading}>
          {loading ? (initial ? 'Saving…' : 'Creating…') : initial ? 'Save Changes' : 'Create Record'}
        </Button>
      </div>
    </form>
  )
}
