import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Field, Input, Checkbox, Button } from '../ui'
import { hostname, ipList } from '../../lib/validation'
import type { DNSServerCreate } from '../../types'

interface DNSServerFormProps {
  loading: boolean
  onSubmit: (payload: DNSServerCreate) => Promise<void>
}

const schema = z.object({
  name: hostname,
  is_recursive: z.boolean(),
  is_authoritative: z.boolean(),
  forwarders: ipList,
})

type FormValues = z.infer<typeof schema>

export function DNSServerForm({ loading, onSubmit }: DNSServerFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: 'dns-server-1',
      is_recursive: true,
      is_authoritative: true,
      forwarders: '1.1.1.1,8.8.8.8',
    },
  })

  const onValid = (values: FormValues) => {
    void onSubmit({
      name: values.name,
      is_recursive: values.is_recursive,
      is_authoritative: values.is_authoritative,
      forwarders: values.forwarders
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean),
    })
  }

  return (
    <form onSubmit={handleSubmit(onValid)} noValidate className="space-y-4">
      <Field label="Name" required error={errors.name?.message}>
        <Input mono {...register('name')} />
      </Field>
      <Field
        label="Forwarders (comma separated)"
        helper="IP addresses of upstream forwarders"
        error={errors.forwarders?.message}
      >
        <Input mono {...register('forwarders')} />
      </Field>
      <div className="flex items-center gap-6 text-sm">
        <label htmlFor="dns-server-recursive" className="inline-flex items-center gap-2 cursor-pointer">
          <Checkbox id="dns-server-recursive" {...register('is_recursive')} />
          Recursive
        </label>
        <label htmlFor="dns-server-authoritative" className="inline-flex items-center gap-2 cursor-pointer">
          <Checkbox id="dns-server-authoritative" {...register('is_authoritative')} />
          Authoritative
        </label>
      </div>
      <div className="flex justify-end">
        <Button type="submit" disabled={loading}>
          {loading ? 'Creating…' : 'Create Server'}
        </Button>
      </div>
    </form>
  )
}
