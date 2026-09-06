import type { ReactNode } from 'react'
import { cn } from '../../lib/utils'

/* -------------------------------------------------------------------------- */
/*  PageHeader                                                                */
/*                                                                            */
/*  Contract:                                                                 */
/*    title            → text-2xl font-semibold text-on-surface               */
/*    description?     → text-sm text-on-surface-muted                        */
/*    primaryAction?   → ReactNode, rendered LAST in action row               */
/*    secondaryActions?→ ReactNode[], rendered FIRST in action row            */
/*    tabs?            → ReactNode, rendered below in a bordered strip        */
/*                                                                            */
/*  DOM order assertion (load-bearing):                                       */
/*    secondaryActions appear BEFORE primaryAction in the DOM.                */
/* -------------------------------------------------------------------------- */

export interface PageHeaderProps {
  /** Page title — always visible. */
  title: string
  /** Optional description below the title. */
  description?: string
  /** Single primary action button/link — rendered LAST in the action row. */
  primaryAction?: ReactNode
  /** Secondary action buttons/links — rendered FIRST in the action row. */
  secondaryActions?: ReactNode[]
  /** Optional tab strip rendered below the header in a bordered container. */
  tabs?: ReactNode
  /** Additional class on the root element. */
  className?: string
}

export function PageHeader({
  title,
  description,
  primaryAction,
  secondaryActions,
  tabs,
  className,
}: PageHeaderProps) {
  const hasActions =
    (secondaryActions != null && secondaryActions.length > 0) ||
    primaryAction != null

  return (
    <div className={cn('w-full', className)}>
      {/* Title + actions row */}
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h1 className="text-2xl font-semibold text-on-surface truncate">
            {title}
          </h1>
          {description != null && description.length > 0 ? (
            <p className="mt-1 text-sm text-on-surface-muted">{description}</p>
          ) : null}
        </div>

        {hasActions ? (
          <div className="flex items-center gap-2 shrink-0">
            {/* SECONDARY actions first */}
            {secondaryActions?.map((action, i) => (
              <span key={i}>{action}</span>
            ))}
            {/* PRIMARY action last */}
            {primaryAction != null ? <span>{primaryAction}</span> : null}
          </div>
        ) : null}
      </div>

      {/* Tab strip */}
      {tabs != null ? (
        <div className="mt-4 border-b border-border">{tabs}</div>
      ) : null}
    </div>
  )
}
