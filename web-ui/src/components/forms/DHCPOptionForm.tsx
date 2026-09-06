import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button, Field, Input } from '../ui'
import { DHCPSubnetType } from '../../types'
import type { DHCPOptionCreate } from '../../types'

interface DHCPOptionFormProps {
  subnetType: DHCPSubnetType
  loading: boolean
  onSubmit: (payload: DHCPOptionCreate) => void
}

const schema = z.object({
  option_code: z.string().refine(
    (value) => /^\d+$/.test(value) && Number(value) <= 255,
    'Option code must be a whole number between 0 and 255',
  ),
  option_name: z.string().trim().min(1, 'Option name is required'),
  option_value: z.string().trim().min(1, 'Option value is required'),
})

type FormValues = z.infer<typeof schema>

export function DHCPOptionForm({ subnetType, loading, onSubmit }: DHCPOptionFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      option_code: subnetType === DHCPSubnetType.V4 ? '66' : '23',
      option_name: subnetType === DHCPSubnetType.V4 ? 'tftp-server-name' : 'dns-servers',
      option_value: subnetType === DHCPSubnetType.V4 ? '192.168.10.2' : '2001:db8::53',
    },
  })

  const onValid = (values: FormValues) => {
    onSubmit({
      option_code: Number(values.option_code),
      option_name: values.option_name,
      option_value: values.option_value,
      type: subnetType,
    })
  }

  return (
    <form onSubmit={handleSubmit(onValid)} noValidate className="space-y-4">
      <Field label="Option Code" required error={errors.option_code?.message}>
        <Input type="number" {...register('option_code')} />
      </Field>
      <Field label="Option Name" required error={errors.option_name?.message}>
        <Input {...register('option_name')} />
      </Field>
      <Field label="Option Value" required error={errors.option_value?.message}>
        <Input mono {...register('option_value')} />
      </Field>
      <div className="flex justify-end">
        <Button type="submit" loading={loading}>
          Create Option
        </Button>
      </div>
    </form>
  )
}
