import { forwardRef, type ButtonHTMLAttributes } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import type { LucideIcon } from 'lucide-react'
import { Loader2 } from 'lucide-react'
import { cn } from '../../lib/utils'
import { Tooltip } from './Tooltip'

/* -------------------------------------------------------------------------- */
/*  Button variants (exported for Link / anchor composition via className)     */
/* -------------------------------------------------------------------------- */

// eslint-disable-next-line react-refresh/only-export-components -- cva variant utility, not a component
export const buttonVariants = cva(
  [
    'inline-flex items-center justify-center gap-2',
    'font-medium whitespace-nowrap',
    'rounded-card',
    'transition-colors',
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-surface',
    'disabled:pointer-events-none disabled:opacity-50',
  ],
  {
    variants: {
      variant: {
        primary:
          'bg-primary text-primary-fg hover:bg-primary-hover',
        secondary:
          'bg-surface-card text-on-surface border border-border hover:bg-surface-elevated',
        ghost:
          'text-on-surface hover:bg-surface-elevated',
        destructive:
          'bg-danger text-danger-fg hover:bg-danger/90',
      },
      size: {
        sm: 'h-8 px-3 text-sm',
        md: 'h-9 px-4 text-sm',
        lg: 'h-10 px-5',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  },
)

/* -------------------------------------------------------------------------- */
/*  Button                                                                     */
/* -------------------------------------------------------------------------- */

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  /** Show a leading icon (LucideIcon component). */
  icon?: LucideIcon
  /** Replaces the icon with a spinning Loader2 and disables the button. */
  loading?: boolean
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, icon: Icon, loading, disabled, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(buttonVariants({ variant, size, className }))}
        disabled={disabled || loading}
        aria-busy={loading || undefined}
        {...props}
      >
        {loading ? (
          <Loader2 className="animate-spin" size={16} />
        ) : Icon ? (
          <Icon size={16} />
        ) : null}
        {children}
      </button>
    )
  },
)
Button.displayName = 'Button'

/* -------------------------------------------------------------------------- */
/*  IconButton                                                                 */
/* -------------------------------------------------------------------------- */

export interface IconButtonProps
  extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'children'>,
    Pick<VariantProps<typeof buttonVariants>, 'variant'> {
  /** LucideIcon component to render. */
  icon: LucideIcon
  /** Accessible label — used for aria-label AND tooltip content. */
  label: string
  /** Icon-button size maps to w/h: sm=32px, md=36px, lg=40px. */
  size?: 'sm' | 'md' | 'lg'
}

const iconButtonSizes = cva('inline-flex items-center justify-center rounded-card', {
  variants: {
    size: {
      sm: 'w-8 h-8',
      md: 'w-9 h-9',
      lg: 'w-10 h-10',
    },
  },
  defaultVariants: {
    size: 'md',
  },
})

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ className, variant = 'ghost', icon: Icon, label, size, ...props }, ref) => {
    return (
      <Tooltip content={label} delayDuration={300} side="top">
        <button
          ref={ref}
          type="button"
          aria-label={label}
          className={cn(
            buttonVariants({ variant, className }),
            iconButtonSizes({ size }),
            'px-0', // remove horizontal padding — square icon button
          )}
          {...props}
        >
          <Icon size={16} />
        </button>
      </Tooltip>
    )
  },
)
IconButton.displayName = 'IconButton'
