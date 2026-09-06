import { forwardRef, type ReactNode } from 'react'
import * as RadixTabs from '@radix-ui/react-tabs'
import { cn } from '../../lib/utils'

/* -------------------------------------------------------------------------- */
/*  Tabs — Radix underline style                                              */
/*                                                                            */
/*  Wraps @radix-ui/react-tabs with friendly props:                           */
/*    items: { value, label }[]          → tab triggers                       */
/*    defaultValue? / value? / onValueChange?                                 */
/*    children                           → content panels                     */
/*                                                                            */
/*  Style: underline active (data-[state=active]:border-b-2 border-primary)   */
/*  Keyboard: roving tabindex via Radix (arrow keys move focus/selection).    */
/*  Controlled + uncontrolled.                                                */
/* -------------------------------------------------------------------------- */

export interface TabItem {
  value: string
  label: string
}

export interface TabsProps {
  /** Tab trigger definitions. */
  items: TabItem[]
  /** Default selected tab (uncontrolled). */
  defaultValue?: string
  /** Selected tab (controlled). */
  value?: string
  /** Callback when tab selection changes. */
  onValueChange?: (value: string) => void
  /** Tab content panels — each child should be a TabsContent or wrapper. */
  children: ReactNode
  /** Additional class on the root element. */
  className?: string
}

export function Tabs({
  items,
  defaultValue,
  value,
  onValueChange,
  children,
  className,
}: TabsProps) {
  return (
    <RadixTabs.Root
      className={cn('w-full', className)}
      defaultValue={defaultValue}
      value={value}
      onValueChange={onValueChange}
    >
      <RadixTabs.List
        className="flex gap-0 border-b border-border"
        aria-label="Tabs"
      >
        {items.map((item) => (
          <RadixTabs.Trigger
            key={item.value}
            value={item.value}
            className={cn(
              'px-4 py-2 text-sm font-medium',
              'border-b-2 -mb-px',
              'transition-colors',
              'text-on-surface-muted',
              'data-[state=active]:border-primary data-[state=active]:text-on-surface',
              'border-transparent',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-surface',
            )}
          >
            {item.label}
          </RadixTabs.Trigger>
        ))}
      </RadixTabs.List>
      {children}
    </RadixTabs.Root>
  )
}

/* -------------------------------------------------------------------------- */
/*  TabsContent — re-export with friendly naming                              */
/* -------------------------------------------------------------------------- */

export interface TabsContentProps {
  /** Tab value this content belongs to. */
  value: string
  /** Content. */
  children: ReactNode
  /** Additional class. */
  className?: string
}

export const TabsContent = forwardRef<HTMLDivElement, TabsContentProps>(
  ({ className, children, value, ...props }, ref) => (
    <RadixTabs.Content
      ref={ref}
      value={value}
      className={cn('pt-4 focus-visible:outline-none', className)}
      {...props}
    >
      {children}
    </RadixTabs.Content>
  ),
)
TabsContent.displayName = 'TabsContent'
