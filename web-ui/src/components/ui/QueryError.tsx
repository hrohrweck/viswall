import { AlertTriangle } from 'lucide-react'
import { Button } from './Button'

interface QueryErrorProps {
  title?: string
  message?: string
  onRetry?: () => void
}

export function QueryError({
  title = 'Something went wrong',
  message,
  onRetry,
}: QueryErrorProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-danger-subtle mb-4">
        <AlertTriangle className="h-6 w-6 text-danger" />
      </div>
      <h3 className="text-lg font-medium text-on-surface mb-1">{title}</h3>
      {message && (
        <p className="text-sm text-on-surface-muted mb-4 max-w-md">{message}</p>
      )}
      {onRetry && (
        <Button variant="secondary" onClick={onRetry}>
          Retry
        </Button>
      )}
    </div>
  )
}
