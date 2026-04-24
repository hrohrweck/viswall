import { useState } from 'react'
import type { User, UserCreate, UserUpdate, Instance } from '../../types'
import { UserRole, AuthBackend } from '../../types'

interface UserCreateFormProps {
  initial?: Partial<User>
  instances: Instance[]
  onSubmit: (data: UserCreate | UserUpdate) => Promise<void>
  onCancel: () => void
  loading: boolean
  isEdit?: boolean
}

export function UserCreateForm({ initial, instances, onSubmit, onCancel, loading, isEdit }: UserCreateFormProps) {
  const [username, setUsername] = useState(initial?.username || '')
  const [email, setEmail] = useState(initial?.email || '')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState<UserRole>((initial?.role as UserRole) || UserRole.USER)
  const [authBackend, setAuthBackend] = useState<AuthBackend>((initial?.auth_backend as AuthBackend) || AuthBackend.LOCAL)
  const [selectedInstances, setSelectedInstances] = useState<number[]>(initial?.instances || [])
  const [isActive, setIsActive] = useState(initial?.is_active ?? true)
  const [error, setError] = useState('')

  const toggleInstance = (id: number) => {
    setSelectedInstances((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    )
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      if (isEdit) {
        await onSubmit({
          email,
          role,
          is_active: isActive,
          instances: selectedInstances,
        } as UserUpdate)
      } else {
        await onSubmit({
          username,
          email,
          password: password || undefined,
          role,
          auth_backend: authBackend,
          instances: selectedInstances,
        } as UserCreate)
      }
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      setError((err as any)?.response?.data?.detail || 'Failed to save user')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            disabled={isEdit}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            required
          />
        </div>
      </div>

      {!isEdit && (
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Min 8 characters"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              minLength={8}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Auth Backend</label>
            <select
              value={authBackend}
              onChange={(e) => setAuthBackend(e.target.value as AuthBackend)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="local">Local</option>
              <option value="ldap">LDAP</option>
              <option value="ad">Active Directory</option>
            </select>
          </div>
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
        <select
          value={role}
          onChange={(e) => setRole(e.target.value as UserRole)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
        >
          <option value="superadmin">Super Admin</option>
          <option value="admin">Admin</option>
          <option value="user">User</option>
          <option value="readonly">Read Only</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Assigned Instances</label>
        <div className="flex flex-wrap gap-2">
          {instances.map((inst) => (
            <button
              key={inst.id}
              type="button"
              onClick={() => toggleInstance(inst.id)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors ${
                selectedInstances.includes(inst.id)
                  ? 'bg-primary-50 border-primary-300 text-primary-700'
                  : 'bg-white border-gray-300 text-gray-600 hover:bg-gray-50'
              }`}
            >
              {inst.name}
            </button>
          ))}
          {instances.length === 0 && (
            <p className="text-sm text-gray-400">No instances available</p>
          )}
        </div>
      </div>

      {isEdit && (
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="isActive"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
            className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
          />
          <label htmlFor="isActive" className="text-sm text-gray-700">Active</label>
        </div>
      )}

      <div className="flex justify-end gap-3 pt-4">
        <button type="button" onClick={onCancel} className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200">
          Cancel
        </button>
        <button type="submit" disabled={loading} className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50">
          {loading ? 'Saving...' : isEdit ? 'Update User' : 'Create User'}
        </button>
      </div>
    </form>
  )
}
