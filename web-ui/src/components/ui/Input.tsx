import { forwardRef, type InputHTMLAttributes, type TextareaHTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

/* -------------------------------------------------------------------------- */
/*  Shared base classes                                                        */
/* -------------------------------------------------------------------------- */

const inputBase = [
  'h-9 w-full rounded-card border border-border bg-surface-card px-3',
  'text-sm text-on-surface placeholder:text-on-surface-muted',
  'transition-colors',
  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary',
  'disabled:cursor-not-allowed disabled:opacity-50',
  'aria-invalid:border-danger aria-invalid:focus-visible:ring-danger',
].join(' ')

/* -------------------------------------------------------------------------- */
/*  Input                                                                      */
/* -------------------------------------------------------------------------- */

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  /** Renders the value in monospace (JetBrains Mono) — for IPs, UUIDs, keys. */
  mono?: boolean
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, mono, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(inputBase, mono && 'font-mono', className)}
      {...props}
    />
  ),
)
Input.displayName = 'Input'

/* -------------------------------------------------------------------------- */
/*  Textarea                                                                   */
/* -------------------------------------------------------------------------- */

export type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement>

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => (
    <textarea
      ref={ref}
      className={cn(
        'min-h-[5rem] w-full rounded-card border border-border bg-surface-card px-3 py-2',
        'text-sm text-on-surface placeholder:text-on-surface-muted',
        'transition-colors',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary',
        'disabled:cursor-not-allowed disabled:opacity-50',
        'aria-invalid:border-danger aria-invalid:focus-visible:ring-danger',
        className,
      )}
      {...props}
    />
  ),
)
Textarea.displayName = 'Textarea'
