import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button, Checkbox, Field, Input, Select } from '../ui'
import { cn } from '../../lib/utils'
import { email } from '../../lib/validation'
import type { Instance, User, UserCreate, UserUpdate } from '../../types'
import { UserRole, AuthBackend } from '../../types'

interface UserCreateFormProps {
  initial?: Partial<User>
  instances: Instance[]
  onSubmit: (data: UserCreate | UserUpdate) => Promise<void>
  onCancel: () => void
  loading: boolean
  isEdit?: boolean
}

const makeSchema = (isEdit: boolean) =>
  z
    .object({
      username: z.string(),
      email: email,
      password: z.string(),
      role: z.nativeEnum(UserRole),
      auth_backend: z.nativeEnum(AuthBackend),
      instances: z.array(z.number()),
      is_active: z.boolean(),
    })
    .superRefine((data, ctx) => {
      if (!isEdit && data.username.trim() === '') {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ['username'],
          message: 'Username is required',
        })
      }
      if (data.password !== '' && data.password.length < 8) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ['password'],
          message: 'Password must be at least 8 characters',
        })
      }
    })

type FormValues = z.infer<ReturnType<typeof makeSchema>>

export function UserCreateForm({ initial, instances, onSubmit, onCancel, loading, isEdit }: UserCreateFormProps) {
  const [submitError, setSubmitError] = useState('')
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(makeSchema(!!isEdit)),
    defaultValues: {
      username: initial?.username || '',
      email: initial?.email || '',
      password: '',
      role: (initial?.role as UserRole) || UserRole.USER,
      auth_backend: (initial?.auth_backend as AuthBackend) || AuthBackend.LOCAL,
      instances: initial?.instances || [],
      is_active: initial?.is_active ?? true,
    },
  })

  const selectedInstances = watch('instances')

  const toggleInstance = (id: number) => {
    setValue(
      'instances',
      selectedInstances.includes(id)
        ? selectedInstances.filter((i) => i !== id)
        : [...selectedInstances, id],
      { shouldValidate: true },
    )
  }

  const onValid = async (values: FormValues): Promise<void> => {
    setSubmitError('')
    try {
      if (isEdit) {
        await onSubmit({
          email: values.email,
          role: values.role,
          is_active: values.is_active,
          instances: values.instances,
        } as UserUpdate)
      } else {
        await onSubmit({
          username: values.username,
          email: values.email,
          password: values.password || undefined,
          role: values.role,
          auth_backend: values.auth_backend,
          instances: values.instances,
        } as UserCreate)
      }
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setSubmitError(detail || 'Failed to save user')
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
        <Field label="Username" required={!isEdit} error={isEdit ? undefined : errors.username?.message}>
          <Input type="text" disabled={isEdit} {...register('username')} />
        </Field>
        <Field label="Email" required error={errors.email?.message}>
          <Input type="email" {...register('email')} />
        </Field>
      </div>

      {!isEdit && (
        <div className="grid grid-cols-2 gap-4">
          <Field label="Password" helper="Min 8 characters" error={errors.password?.message}>
            <Input type="password" placeholder="Min 8 characters" {...register('password')} />
          </Field>
          <Field label="Auth Backend">
            <Select {...register('auth_backend')}>
              <option value="local">Local</option>
              <option value="ldap">LDAP</option>
              <option value="ad">Active Directory</option>
            </Select>
          </Field>
        </div>
      )}

      <Field label="Role">
        <Select {...register('role')}>
          <option value="superadmin">Super Admin</option>
          <option value="admin">Admin</option>
          <option value="user">User</option>
          <option value="readonly">Read Only</option>
        </Select>
      </Field>

      <div>
        <span className="block text-sm font-medium text-on-surface mb-2">Assigned Instances</span>
        <div className="flex flex-wrap gap-2">
          {instances.map((inst) => (
            <button
              key={inst.id}
              type="button"
              onClick={() => toggleInstance(inst.id)}
              aria-pressed={selectedInstances.includes(inst.id)}
              className={cn(
                'px-3 py-1.5 rounded-card text-sm font-medium border transition-colors',
                selectedInstances.includes(inst.id)
                  ? 'bg-primary-subtle border-primary text-primary'
                  : 'bg-surface-card border-border text-on-surface-muted hover:bg-surface-elevated',
              )}
            >
              {inst.name}
            </button>
          ))}
          {instances.length === 0 && (
            <p className="text-sm text-on-surface-muted">No instances available</p>
          )}
        </div>
      </div>

      {isEdit && (
        <div className="flex items-center gap-2">
          <Checkbox id="isActive" {...register('is_active')} />
          <label htmlFor="isActive" className="text-sm text-on-surface">
            Active
          </label>
        </div>
      )}

      <div className="flex justify-end gap-3 pt-4">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" loading={loading}>
          {loading ? 'Saving...' : isEdit ? 'Update User' : 'Create User'}
        </Button>
      </div>
    </form>
  )
}
