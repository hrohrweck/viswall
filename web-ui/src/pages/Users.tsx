import { useState } from 'react'
import { Plus, UserPlus, Pencil, Trash2 } from 'lucide-react'
import { useUsers, useCreateUser, useUpdateUser, useDeleteUser, useInstances } from '../hooks/useApi'
import {
  PageHeader,
  Button,
  DataTable,
  Modal,
  ConfirmDialog,
  RoleBadge,
  AuthBackendBadge,
  Switch,
  EmptyState,
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  toast,
} from '../components/ui'
import { UserCreateForm } from '../components/forms/UserCreateForm'
import type { User, UserCreate, UserUpdate } from '../types'
import { formatDistanceToNow } from 'date-fns'
import { getErrMsg } from '../lib/utils'

export function Users() {
  const { data: users, isLoading, isError, refetch } = useUsers()
  const { data: instances } = useInstances()
  const createMutation = useCreateUser()
  const updateMutation = useUpdateUser()
  const deleteMutation = useDeleteUser()

  const [showCreate, setShowCreate] = useState(false)
  const [editTarget, setEditTarget] = useState<User | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<User | null>(null)
  const [toggleTarget, setToggleTarget] = useState<User | null>(null)

  /* ── Confirm-before-fire: toggle active ── */
  const handleToggleConfirm = () => {
    if (!toggleTarget) return
    updateMutation.mutate(
      { id: toggleTarget.id, is_active: !toggleTarget.is_active },
      {
        onSuccess: () => {
          toast.success(`User ${toggleTarget.username} ${toggleTarget.is_active ? 'deactivated' : 'activated'}`)
          setToggleTarget(null)
        },
        onError: (e) => {
          toast.error(getErrMsg(e))
          setToggleTarget(null)
        },
      },
    )
  }

  /* ── Create ── */
  const handleCreate = async (data: UserCreate | UserUpdate) => {
    await createMutation.mutateAsync(data as UserCreate)
    toast.success('User created')
    setShowCreate(false)
  }

  /* ── Edit ── */
  const handleUpdate = async (data: UserUpdate) => {
    if (editTarget) {
      await updateMutation.mutateAsync({ id: editTarget.id, ...data })
      toast.success('User updated')
      setEditTarget(null)
    }
  }

  /* ── Delete ── */
  const handleDelete = () => {
    if (!deleteTarget) return
    deleteMutation.mutate(deleteTarget.id, {
      onSuccess: () => {
        toast.success('User deleted')
        setDeleteTarget(null)
      },
      onError: (e) => {
        toast.error(getErrMsg(e))
        setDeleteTarget(null)
      },
    })
  }

  /* ── Column defs ── */
  const columns = [
    {
      key: 'username',
      header: 'User',
      render: (user: User) => (
        <div>
          <p className="font-medium text-on-surface">{user.username}</p>
          <p className="text-xs text-on-surface-muted">{user.email}</p>
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
      key: 'active',
      header: 'Active',
      render: (user: User) => (
        <Switch
          checked={user.is_active}
          onCheckedChange={() => setToggleTarget(user)}
          aria-label={`Toggle active for ${user.username}`}
        />
      ),
    },
    {
      key: 'last_login',
      header: 'Last Login',
      render: (user: User) => (
        <span className="text-sm text-on-surface-muted">
          {user.last_login
            ? formatDistanceToNow(new Date(user.last_login), { addSuffix: true })
            : 'Never'}
        </span>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title="Users"
        description="Manage user accounts and access permissions."
        primaryAction={
          <Button icon={UserPlus} onClick={() => setShowCreate(true)}>
            Add user
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={users || []}
        keyExtractor={(user) => user.id}
        enableSorting
        searchable
        searchPlaceholder="Search users..."
        pagination
        isLoading={isLoading}
        isError={isError}
        onRetry={() => refetch()}
        rowActions={(user) => (
          <DropdownMenu>
            <DropdownMenuTrigger label="User actions" />
            <DropdownMenuContent>
              <DropdownMenuItem onClick={() => setEditTarget(user)}>
                <Pencil className="mr-2 h-4 w-4" />
                Edit
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                danger
                onClick={(e) => {
                  e.stopPropagation()
                  setDeleteTarget(user)
                }}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
        emptyContent={
          <EmptyState
            icon={Plus}
            title="No users"
            description="Create your first user to get started."
            actionLabel="Add user"
            onAction={() => setShowCreate(true)}
          />
        }
      />

      {/* ── Create modal ── */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Create User" size="lg">
        <UserCreateForm
          instances={instances || []}
          onSubmit={handleCreate}
          onCancel={() => setShowCreate(false)}
          loading={createMutation.isPending}
        />
      </Modal>

      {/* ── Edit modal ── */}
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

      {/* ── Toggle confirm ── */}
      <ConfirmDialog
        open={!!toggleTarget}
        onClose={() => setToggleTarget(null)}
        onConfirm={handleToggleConfirm}
        title={toggleTarget?.is_active ? 'Deactivate User' : 'Activate User'}
        message={toggleTarget ? `Are you sure you want to ${toggleTarget.is_active ? 'deactivate' : 'activate'} "${toggleTarget.username}"?` : ''}
        impact={toggleTarget ? `Changes whether ${toggleTarget.username} can sign in.` : undefined}
        confirmLabel={toggleTarget?.is_active ? 'Deactivate' : 'Activate'}
        variant="warning"
        loading={updateMutation.isPending}
      />

      {/* ── Delete confirm ── */}
      <ConfirmDialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Delete User"
        message={`Are you sure you want to delete "${deleteTarget?.username}"?`}
        impact="This action permanently removes all user data and cannot be undone."
        loading={deleteMutation.isPending}
      />
    </div>
  )
}
