import { Link } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'
import { cn } from '../../lib/utils'

/* -------------------------------------------------------------------------- */
/*  Breadcrumbs                                                               */
/*                                                                            */
/*  Contract:                                                                 */
/*    items: { label, to? }[]                                                */
/*    → nav aria-label="Breadcrumb"                                          */
/*    → ol > li with ChevronRight separators                                 */
/*    → links for items with `to` (react-router Link)                        */
/*    → plain text for last item (aria-current="page")                       */
/* -------------------------------------------------------------------------- */

export interface BreadcrumbItem {
  label: string
  /** Route path — omit for the last item (renders as plain text). */
  to?: string
}

export interface BreadcrumbsProps {
  /** Ordered breadcrumb items. */
  items: BreadcrumbItem[]
  /** Additional class on the nav element. */
  className?: string
}

export function Breadcrumbs({ items, className }: BreadcrumbsProps) {
  if (items.length === 0) return null

  return (
    <nav aria-label="Breadcrumb" className={cn('text-sm', className)}>
      <ol className="flex items-center gap-1.5">
        {items.map((item, index) => {
          const isLast = index === items.length - 1

          return (
            <li key={index} className="flex items-center gap-1.5">
              {index > 0 ? (
                <ChevronRight
                  size={14}
                  className="text-on-surface-muted shrink-0"
                  aria-hidden="true"
                />
              ) : null}
              {isLast ? (
                <span
                  aria-current="page"
                  className="text-on-surface font-medium"
                >
                  {item.label}
                </span>
              ) : item.to != null ? (
                <Link
                  to={item.to}
                  className="text-on-surface-muted hover:text-on-surface transition-colors"
                >
                  {item.label}
                </Link>
              ) : (
                <span className="text-on-surface-muted">{item.label}</span>
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
