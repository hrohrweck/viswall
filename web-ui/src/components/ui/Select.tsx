import { forwardRef, type SelectHTMLAttributes } from 'react'
import { ChevronDown } from 'lucide-react'
import { cn } from '../../lib/utils'

/* -------------------------------------------------------------------------- */
/*  Select — native <select> with custom chevron (accessible by default)      */
/* -------------------------------------------------------------------------- */

export type SelectProps = SelectHTMLAttributes<HTMLSelectElement>

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, children, ...props }, ref) => (
    <div className="relative">
      <select
        ref={ref}
        className={cn(
          'h-9 w-full appearance-none rounded-card border border-border bg-surface-card',
          'pl-3 pr-8 text-sm text-on-surface',
          'transition-colors',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary',
          'disabled:cursor-not-allowed disabled:opacity-50',
          'aria-invalid:border-danger aria-invalid:focus-visible:ring-danger',
          className,
        )}
        {...props}
      >
        {children}
      </select>
      <ChevronDown
        size={16}
        className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-on-surface-muted"
        aria-hidden="true"
      />
    </div>
  ),
)
Select.displayName = 'Select'
