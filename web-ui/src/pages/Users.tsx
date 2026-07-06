import { useState } from 'react'
import { Plus, UserPlus } from 'lucide-react'
import {
  useUsers,
  useCreateUser,
  useUpdateUser,
  useDeleteUser,
  useInstances,
} from '../hooks/useApi'
import {
  DataTable,
  Modal,
  ConfirmDialog,
  RoleBadge,
  AuthBackendBadge,
  StatusBadge,
  LoadingSpinner,
  EmptyState,
} from '../components/ui'
import { UserCreateForm } from '../components/forms/UserCreateForm'
import type { User, UserCreate, UserUpdate } from '../types'
import { formatDistanceToNow } from 'date-fns'

export function Users() {
  const { data: users, isLoading } = useUsers()
  const { data: instances } = useInstances()
  const createMutation = useCreateUser()
  const updateMutation = useUpdateUser()
  const deleteMutation = useDeleteUser()
  const [showCreate, setShowCreate] = useState(false)
  const [editTarget, setEditTarget] = useState<User | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<User | null>(null)

  const handleCreate = async (data: UserCreate | UserUpdate) => {
    await createMutation.mutateAsync(data as UserCreate)
    setShowCreate(false)
  }

  const handleUpdate = async (data: UserUpdate) => {
    if (editTarget) {
      await updateMutation.mutateAsync({ id: editTarget.id, ...data })
      setEditTarget(null)
    }
  }

  const handleDelete = async () => {
    if (deleteTarget) {
      await deleteMutation.mutateAsync(deleteTarget.id)
      setDeleteTarget(null)
    }
  }

  const handleToggleActive = async (user: User) => {
    await updateMutation.mutateAsync({ id: user.id, is_active: !user.is_active })
  }

  if (isLoading) return <LoadingSpinner />

  const columns = [
    {
      key: 'username',
      header: 'User',
      render: (user: User) => (
        <div>
          <p className="font-medium text-gray-900 dark:text-white">{user.username}</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">{user.email}</p>
        </div>
      ),
    },
    {
      key: 'role',
      header: 'Role',
      render: (user: User) => <RoleBadge role={user.role} />,
    },
    {
      key: 'auth_backend',
      header: 'Auth',
      render: (user: User) => <AuthBackendBadge backend={user.auth_backend} />,
    },
    {
      key: 'status',
      header: 'Status',
      render: (user: User) => (
        <button onClick={() => handleToggleActive(user)}>
          <StatusBadge status={user.is_active ? 'active' : 'inactive'} />
        </button>
      ),
    },
    {
      key: 'instances',
      header: 'Instances',
      render: (user: User) => (
        <span className="text-sm text-gray-600 dark:text-gray-400">
          {user.instances.length > 0
            ? `${user.instances.length} assigned`
            : 'None'}
        </span>
      ),
    },
    {
      key: 'last_login',
      header: 'Last Login',
      render: (user: User) => (
        <span className="text-sm text-gray-500 dark:text-gray-400">
          {user.last_login
            ? formatDistanceToNow(new Date(user.last_login), { addSuffix: true })
            : 'Never'}
        </span>
      ),
    },
    {
      key: 'actions',
      header: '',
      render: (user: User) => (
        <div className="flex items-center gap-2">
          <button onClick={() => setEditTarget(user)} className="text-sm text-primary-600 hover:text-primary-700">
            Edit
          </button>
          <button onClick={() => setDeleteTarget(user)} className="text-sm text-red-600 hover:text-red-700">
            Delete
          </button>
        </div>
      ),
    },
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Users</h2>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          <UserPlus className="w-5 h-5" />
          Add User
        </button>
      </div>

      <DataTable
        columns={columns}
        data={users || []}
        keyExtractor={(user) => user.id}
        emptyContent={
          <EmptyState
            icon={Plus}
            title="No users"
            description="Create your first user to get started."
            actionLabel="Add User"
            onAction={() => setShowCreate(true)}
          />
        }
      />

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Create User" size="lg">
        <UserCreateForm
          instances={instances || []}
          onSubmit={handleCreate}
          onCancel={() => setShowCreate(false)}
          loading={createMutation.isPending}
        />
      </Modal>

      <Modal open={!!editTarget} onClose={() => setEditTarget(null)} title="Edit User" size="lg">
        {editTarget && (
          <UserCreateForm
            initial={editTarget}
            instances={instances || []}
            onSubmit={handleUpdate}
            onCancel={() => setEditTarget(null)}
            loading={updateMutation.isPending}
            isEdit
          />
        )}
      </Modal>

      <ConfirmDialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Delete User"
        message={`Are you sure you want to delete "${deleteTarget?.username}"?`}
        loading={deleteMutation.isPending}
      />
    </div>
  )
}
