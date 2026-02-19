import { BarChart3 } from 'lucide-react'

export function Metrics() {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Metrics</h2>
      
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
        <BarChart3 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Metrics Dashboard</h3>
        <p className="text-gray-600">View system metrics and statistics.</p>
      </div>
    </div>
  )
}
