import { Users } from 'lucide-react'

export function Users() {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Users</h2>
      
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
        <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">User Management</h3>
        <p className="text-gray-600">Manage system users and permissions.</p>
      </div>
    </div>
  )
}
