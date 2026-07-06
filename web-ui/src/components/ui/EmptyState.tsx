import { type LucideIcon } from 'lucide-react'
import { Link } from 'react-router-dom'

interface EmptyStateProps {
  icon: LucideIcon
  title: string
  description: string
  actionLabel?: string
  actionTo?: string
  onAction?: () => void
}

export function EmptyState({ icon: Icon, title, description, actionLabel, actionTo, onAction }: EmptyStateProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 dark:bg-gray-900 dark:border-gray-700">
      <div className="p-12 text-center">
        <Icon className="w-16 h-16 text-gray-300 mx-auto mb-4 dark:text-gray-600" />
        <h3 className="text-lg font-medium text-gray-900 mb-2 dark:text-white">{title}</h3>
        <p className="text-gray-600 mb-6 dark:text-gray-400">{description}</p>
        {actionLabel && (actionTo ? (
          <Link
            to={actionTo}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            {actionLabel}
          </Link>
        ) : onAction ? (
          <button
            onClick={onAction}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            {actionLabel}
          </button>
        ) : null)}
      </div>
    </div>
  )
}
