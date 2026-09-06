import { type LucideIcon } from 'lucide-react'
import { Link } from 'react-router-dom'
import { cn } from '../../lib/utils'
import { Button, buttonVariants } from './Button'

interface EmptyStateProps {
  icon: LucideIcon
  title: string
  description: string
  actionLabel?: string
  actionTo?: string
  onAction?: () => void
  className?: string
}

export function EmptyState({ icon: Icon, title, description, actionLabel, actionTo, onAction, className }: EmptyStateProps) {
  return (
    <div className={cn('bg-surface-card rounded-card border border-border', className)}>
      <div className="p-12 text-center">
        <Icon className="w-16 h-16 text-on-surface-muted mx-auto mb-4" />
        <h3 className="text-lg font-medium text-on-surface mb-2">{title}</h3>
        <p className="text-on-surface-muted mb-6">{description}</p>
        {actionLabel && (actionTo ? (
          <Link to={actionTo} className={cn(buttonVariants({ variant: 'primary' }))}>
            {actionLabel}
          </Link>
        ) : onAction ? (
          <Button onClick={onAction}>{actionLabel}</Button>
        ) : null)}
      </div>
    </div>
  )
}
