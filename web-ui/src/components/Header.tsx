import { Shield } from 'lucide-react'
import { useAuthStore } from '../stores/auth'

export function Header() {
  const { user, logout } = useAuthStore()

  return (
    <header className="bg-white border-b border-gray-200">
      <div className="px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="w-8 h-8 text-primary-600" />
          <h1 className="text-xl font-bold text-gray-900">Viswall</h1>
        </div>
        
        <div className="flex items-center gap-4">
          {user && (
            <>
              <span className="text-sm text-gray-600">{user.username}</span>
              <button
                onClick={logout}
                className="text-sm text-red-600 hover:text-red-700"
              >
                Logout
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
