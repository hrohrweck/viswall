import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button, Checkbox, Field, Input, Select } from '../ui'
import { FirewallAction } from '../../types'
import type { FirewallRuleCreate, FirewallRuleUpdate } from '../../types'
import { anyIpOrCidr, hostname, nonEmptyName, portRange } from '../../lib/validation'

interface FirewallRuleFormProps {
  initial?: Partial<FirewallRuleCreate & { id: number }>
  onSubmit: (data: FirewallRuleCreate | FirewallRuleUpdate) => Promise<void>
  onCancel: () => void
  loading: boolean
}

const isSelectorValueValid = (type: string, value: string): boolean => {
  if (type === 'ip' || type === 'network') return anyIpOrCidr.safeParse(value).success
  if (type === 'interface') return hostname.safeParse(value).success
  return true
}

const selectorValueError = (type: string): string => {
  if (type === 'ip') return 'Enter a valid IP address'
  if (type === 'network') return 'Enter a valid network CIDR'
  return 'Enter a valid interface name (e.g. eth0)'
}

const schema = z
  .object({
    name: nonEmptyName,
    description: z.string(),
    source_type: z.string(),
    source_value: z.string(),
    dest_type: z.string(),
    dest_value: z.string(),
    service_protocol: z.string(),
    service_ports: z.string(),
    action: z.nativeEnum(FirewallAction),
    log_enabled: z.boolean(),
  })
  .superRefine((data, ctx) => {
    if (data.source_type !== 'any' && !isSelectorValueValid(data.source_type, data.source_value)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['source_value'],
        message: selectorValueError(data.source_type),
      })
    }
    if (data.dest_type !== 'any' && !isSelectorValueValid(data.dest_type, data.dest_value)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['dest_value'],
        message: selectorValueError(data.dest_type),
      })
    }
    if (data.service_ports !== '' && !portRange.safeParse(data.service_ports).success) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['service_ports'],
        message: 'Enter ports as 80, 443 or 1000-2000',
      })
    }
  })

type FormValues = z.infer<typeof schema>

export function FirewallRuleForm({ initial, onSubmit, onCancel, loading }: FirewallRuleFormProps) {
  const [submitError, setSubmitError] = useState('')
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: initial?.name || '',
      description: initial?.description || '',
      source_type: initial?.source_type || 'any',
      source_value: initial?.source_value || '',
      dest_type: initial?.dest_type || 'any',
      dest_value: initial?.dest_value || '',
      service_protocol: initial?.service_protocol || 'tcp',
      service_ports: initial?.service_ports || '',
      action: initial?.action || FirewallAction.ACCEPT,
      log_enabled: initial?.log_enabled || false,
    },
  })

  const sourceType = watch('source_type')
  const destType = watch('dest_type')

  const onValid = async (values: FormValues): Promise<void> => {
    setSubmitError('')
    try {
      await onSubmit({
        name: values.name,
        description: values.description || undefined,
        source_type: values.source_type,
        source_value: values.source_type !== 'any' ? values.source_value : undefined,
        dest_type: values.dest_type,
        dest_value: values.dest_type !== 'any' ? values.dest_value : undefined,
        service_protocol: values.service_protocol,
        service_ports: values.service_ports || undefined,
        action: values.action,
        log_enabled: values.log_enabled,
      })
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setSubmitError(detail || 'Failed to save rule')
    }
  }

  return (
    <form onSubmit={handleSubmit(onValid)} noValidate className="space-y-4">
      {submitError && (
        <div className="p-3 rounded-card border border-danger bg-danger-subtle text-danger text-sm">
          {submitError}
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <Field label="Rule Name" required error={errors.name?.message}>
          <Input type="text" placeholder="e.g. Allow HTTPS" {...register('name')} />
        </Field>
        <Field label="Description">
          <Input type="text" {...register('description')} />
        </Field>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Field label="Source Type">
          <Select {...register('source_type')}>
            <option value="any">Any</option>
            <option value="ip">IP Address</option>
            <option value="network">Network (CIDR)</option>
            <option value="interface">Interface</option>
          </Select>
        </Field>
        {sourceType !== 'any' && (
          <Field label="Source Value" error={errors.source_value?.message}>
            <Input
              type="text"
              mono
              placeholder={sourceType === 'network' ? '10.0.0.0/8 or 2001:db8::/64' : 'eth0'}
              {...register('source_value')}
            />
          </Field>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Field label="Destination Type">
          <Select {...register('dest_type')}>
            <option value="any">Any</option>
            <option value="ip">IP Address</option>
            <option value="network">Network (CIDR)</option>
            <option value="interface">Interface</option>
          </Select>
        </Field>
        {destType !== 'any' && (
          <Field label="Destination Value" error={errors.dest_value?.message}>
            <Input
              type="text"
              mono
              placeholder={destType === 'network' ? '192.168.1.0/24 or fd00::/64' : 'eth1'}
              {...register('dest_value')}
            />
          </Field>
        )}
      </div>

      <div className="grid grid-cols-3 gap-4">
        <Field label="Protocol">
          <Select {...register('service_protocol')}>
            <option value="tcp">TCP</option>
            <option value="udp">UDP</option>
            <option value="icmp">ICMP</option>
            <option value="any">Any</option>
          </Select>
        </Field>
        <Field label="Ports" error={errors.service_ports?.message}>
          <Input
            type="text"
            mono
            placeholder="e.g. 80, 443 or 1000-2000"
            {...register('service_ports')}
          />
        </Field>
        <Field label="Action">
          <Select {...register('action')}>
            <option value="accept">Accept</option>
            <option value="drop">Drop</option>
            <option value="reject">Reject</option>
          </Select>
        </Field>
      </div>

      <div className="flex items-center gap-2">
        <Checkbox id="logEnabled" {...register('log_enabled')} />
        <label htmlFor="logEnabled" className="text-sm text-on-surface">
          Log matched packets
        </label>
      </div>

      <div className="flex justify-end gap-3 pt-4">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" loading={loading}>
          {loading ? 'Saving...' : 'Save Rule'}
        </Button>
      </div>
    </form>
  )
}
