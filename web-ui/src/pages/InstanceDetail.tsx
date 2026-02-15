import { useParams } from 'react-router-dom'

export function InstanceDetail() {
  const { id } = useParams()
  
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Instance #{id}</h2>
      <p className="text-gray-600">Instance details page - coming soon.</p>
    </div>
  )
}
