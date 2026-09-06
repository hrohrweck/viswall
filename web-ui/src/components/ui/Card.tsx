import { forwardRef, type HTMLAttributes, type ReactNode } from 'react'
import { cn } from '../../lib/utils'

/* -------------------------------------------------------------------------- */
/*  Card — compound component                                                 */
/*                                                                            */
/*  Card({ title?, actions?, children, className?, padding? })                */
/*    → rounded-card border border-border bg-surface-card (NO shadow)        */
/*    → optional header row: title left, actions right                        */
/*    → body p-5 (or custom padding via padding prop)                         */
/*                                                                            */
/*  Sub-components exported for advanced composition:                         */
/*    CardHeader, CardTitle, CardActions, CardBody                            */
/* -------------------------------------------------------------------------- */

/* ---- CardBody ------------------------------------------------------------ */

export interface CardBodyProps extends HTMLAttributes<HTMLDivElement> {
  /** Override default p-5 padding. */
  padding?: string
}

export const CardBody = forwardRef<HTMLDivElement, CardBodyProps>(
  ({ className, padding = 'p-5', children, ...props }, ref) => (
    <div ref={ref} className={cn(padding, className)} {...props}>
      {children}
    </div>
  ),
)
CardBody.displayName = 'CardBody'

/* ---- CardTitle ----------------------------------------------------------- */

export const CardTitle = forwardRef<
  HTMLHeadingElement,
  HTMLAttributes<HTMLHeadingElement>
>(({ className, children, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn('text-base font-semibold text-on-surface', className)}
    {...props}
  >
    {children}
  </h3>
))
CardTitle.displayName = 'CardTitle'

/* ---- CardActions --------------------------------------------------------- */

export const CardActions = forwardRef<
  HTMLDivElement,
  HTMLAttributes<HTMLDivElement>
>(({ className, children, ...props }, ref) => (
  <div ref={ref} className={cn('flex items-center gap-2', className)} {...props}>
    {children}
  </div>
))
CardActions.displayName = 'CardActions'

/* ---- CardHeader ---------------------------------------------------------- */

export interface CardHeaderProps
  extends Omit<HTMLAttributes<HTMLDivElement>, 'title'> {
  /** Title content — rendered left. */
  title?: ReactNode
  /** Actions content — rendered right. */
  actions?: ReactNode
}

export const CardHeader = forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ className, title, actions, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'flex items-center justify-between px-5 py-4 border-b border-border',
        className,
      )}
      {...props}
    >
      {title != null ? (
        typeof title === 'string' ? <CardTitle>{title}</CardTitle> : title
      ) : null}
      {actions != null ? <CardActions>{actions}</CardActions> : null}
      {children}
    </div>
  ),
)
CardHeader.displayName = 'CardHeader'

/* ---- Card (top-level convenience) ---------------------------------------- */

export interface CardProps
  extends Omit<HTMLAttributes<HTMLDivElement>, 'title'> {
  /** Title string or ReactNode — renders a header row when present. */
  title?: ReactNode
  /** Actions rendered right of the title header. */
  actions?: ReactNode
  /** Override default p-5 body padding. */
  padding?: string
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, title, actions, padding, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'rounded-card border border-border bg-surface-card',
        className,
      )}
      {...props}
    >
      {title != null || actions != null ? (
        <CardHeader title={title} actions={actions} />
      ) : null}
      <CardBody padding={padding}>{children}</CardBody>
    </div>
  ),
)
Card.displayName = 'Card'
