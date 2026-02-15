import { Shield } from 'lucide-react'

export function FirewallRules() {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Firewall Rules</h2>
      
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
        <Shield className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Firewall Management</h3>
        <p className="text-gray-600">Select an instance to manage firewall rules.</p>
      </div>
    </div>
  )
}
