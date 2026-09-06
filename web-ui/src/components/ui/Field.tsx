import {
  cloneElement,
  forwardRef,
  isValidElement,
  useId,
  type LabelHTMLAttributes,
  type ReactElement,
  type ReactNode,
} from 'react'
import { AlertTriangle } from 'lucide-react'
import { cn } from '../../lib/utils'

/* -------------------------------------------------------------------------- */
/*  Label                                                                      */
/* -------------------------------------------------------------------------- */

export type LabelProps = LabelHTMLAttributes<HTMLLabelElement>

export const Label = forwardRef<HTMLLabelElement, LabelProps>(
  // htmlFor must be explicit (not spread) for jsx-a11y static verification
  ({ className, htmlFor, ...props }, ref) => (
    <label
      ref={ref}
      htmlFor={htmlFor}
      className={cn('text-sm font-medium text-on-surface', className)}
      {...props}
    />
  ),
)
Label.displayName = 'Label'

/* -------------------------------------------------------------------------- */
/*  Field wrapper — label + control + helper/error with ARIA wiring            */
/* -------------------------------------------------------------------------- */

export interface FieldProps {
  /** Visible label text. */
  label: string
  /** Helper text displayed below the control when no error is present. */
  helper?: string
  /** Error message — takes precedence over `helper`; shown with danger styling. */
  error?: string
  /** Adds a required indicator to the label. */
  required?: boolean
  /** The form control to render (Input, Select, etc.). */
  children: ReactNode
  /** Explicit htmlFor override — auto-generated from useId when omitted. */
  htmlFor?: string
}

export function Field({
  label,
  helper,
  error,
  required,
  children,
  htmlFor: htmlForProp,
}: FieldProps) {
  const autoId = useId()
  const inputId = htmlForProp ?? `field-${autoId}`
  const helperId = `helper-${autoId}`
  const errorId = `error-${autoId}`

  const describedById = error ? errorId : helper ? helperId : undefined

  /* Clone the child element to inject ARIA wiring — only if the child is a
     valid React element that can accept additional props. */
  let control = children
  if (isValidElement(children) && describedById) {
    control = cloneElement(children as ReactElement<Record<string, unknown>>, {
      id: inputId,
      'aria-describedby': describedById,
      ...(error ? { 'aria-invalid': true } : {}),
    })
  } else if (isValidElement(children)) {
    control = cloneElement(children as ReactElement<Record<string, unknown>>, {
      id: inputId,
    })
  }

  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={inputId}>
        {label}
        {required && (
          <span className="ml-0.5 text-danger" aria-hidden="true">
            *
          </span>
        )}
      </Label>

      {control}

      {error && (
        <p id={errorId} role="alert" className="flex items-center gap-1 text-xs text-danger">
          <AlertTriangle size={14} aria-hidden="true" />
          {error}
        </p>
      )}

      {!error && helper && (
        <p id={helperId} className="text-xs text-on-surface-muted">
          {helper}
        </p>
      )}
    </div>
  )
}
Field.displayName = 'Field'
