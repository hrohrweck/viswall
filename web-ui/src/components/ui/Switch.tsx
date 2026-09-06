import { forwardRef, useId, type InputHTMLAttributes } from 'react'
import * as RadixSwitch from '@radix-ui/react-switch'
import { cn } from '../../lib/utils'

/* -------------------------------------------------------------------------- */
/*  Switch — Radix-backed toggle                                               */
/* -------------------------------------------------------------------------- */

export interface SwitchProps {
  /** Controlled checked state. */
  checked?: boolean
  /** Default checked state (uncontrolled). */
  defaultChecked?: boolean
  /** Fires when the toggle state changes. */
  onCheckedChange?: (checked: boolean) => void
  /** Disables the switch. */
  disabled?: boolean
  /** Accessible label. */
  'aria-label'?: string
  /** Additional class on the root button. */
  className?: string
}

export const Switch = forwardRef<HTMLButtonElement, SwitchProps>(
  ({ className, ...props }, ref) => (
    <RadixSwitch.Root
      ref={ref}
      className={cn(
        'relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full',
        'border-2 border-transparent transition-colors',
        'data-[state=checked]:bg-primary data-[state=unchecked]:bg-border',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary',
        'disabled:cursor-not-allowed disabled:opacity-50',
        className,
      )}
      {...props}
    >
      <RadixSwitch.Thumb
        className={cn(
          'pointer-events-none block h-4 w-4 rounded-full bg-white shadow-sm',
          'transition-transform',
          'data-[state=checked]:translate-x-4 data-[state=unchecked]:translate-x-0',
        )}
      />
    </RadixSwitch.Root>
  ),
)
Switch.displayName = 'Switch'

/* -------------------------------------------------------------------------- */
/*  Checkbox — native, accent-coloured                                         */
/* -------------------------------------------------------------------------- */

export type CheckboxProps = Omit<InputHTMLAttributes<HTMLInputElement>, 'type'>

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className, id: idProp, ...props }, ref) => {
    const autoId = useId()
    const id = idProp ?? `checkbox-${autoId}`
    return (
      <input
        ref={ref}
        type="checkbox"
        id={id}
        className={cn(
          'h-4 w-4 rounded border-border accent-primary',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary',
          'disabled:cursor-not-allowed disabled:opacity-50',
          className,
        )}
        {...props}
      />
    )
  },
)
Checkbox.displayName = 'Checkbox'

/* -------------------------------------------------------------------------- */
/*  Radio — native, accent-coloured                                            */
/* -------------------------------------------------------------------------- */

export type RadioProps = Omit<InputHTMLAttributes<HTMLInputElement>, 'type'>

export const Radio = forwardRef<HTMLInputElement, RadioProps>(
  ({ className, id: idProp, ...props }, ref) => {
    const autoId = useId()
    const id = idProp ?? `radio-${autoId}`
    return (
      <input
        ref={ref}
        type="radio"
        id={id}
        className={cn(
          'h-4 w-4 border-border accent-primary',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary',
          'disabled:cursor-not-allowed disabled:opacity-50',
          className,
        )}
        {...props}
      />
    )
  },
)
Radio.displayName = 'Radio'
