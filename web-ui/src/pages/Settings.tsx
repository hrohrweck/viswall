import { Settings as SettingsIcon } from 'lucide-react'

export function Settings() {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Settings</h2>
      
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
        <SettingsIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">System Settings</h3>
        <p className="text-gray-600">Configure system settings and preferences.</p>
      </div>
    </div>
  )
}
