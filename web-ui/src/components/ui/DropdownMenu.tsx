import { ComponentProps, ReactNode } from 'react'
import * as DropdownMenuPrimitive from '@radix-ui/react-dropdown-menu'
import { MoreVertical } from 'lucide-react'
import { cn } from '../../lib/utils'

/* ── Trigger ── */
interface TriggerProps {
  label?: string
  className?: string
}

function Trigger({ label = 'Actions', className }: TriggerProps) {
  return (
    <DropdownMenuPrimitive.Trigger asChild>
      <button
        aria-label={label}
        className={cn(
          'inline-flex items-center justify-center w-9 h-9 rounded-lg',
          'text-on-surface-muted hover:text-on-surface hover:bg-surface-elevated',
          'focus:outline-none focus:ring-2 focus:ring-primary/50',
          className,
        )}
      >
        <MoreVertical className="w-4 h-4" />
      </button>
    </DropdownMenuPrimitive.Trigger>
  )
}

/* ── Content ── */
function Content({ children, className, ...props }: ComponentProps<typeof DropdownMenuPrimitive.Content>) {
  return (
    <DropdownMenuPrimitive.Portal>
      <DropdownMenuPrimitive.Content
        side="bottom"
        align="end"
        sideOffset={4}
        className={cn(
          'z-50 min-w-[8rem] p-1 rounded-card shadow-md border border-border',
          'bg-surface-card text-on-surface',
          'animate-in fade-in-0 zoom-in-95',
          'data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95',
          'data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2',
          'data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2',
          className,
        )}
        {...props}
      >
        {children}
      </DropdownMenuPrimitive.Content>
    </DropdownMenuPrimitive.Portal>
  )
}

/* ── Item ── */
interface ItemProps extends ComponentProps<typeof DropdownMenuPrimitive.Item> {
  danger?: boolean
}

function Item({ danger, className, ...props }: ItemProps) {
  return (
    <DropdownMenuPrimitive.Item
      className={cn(
        'relative flex cursor-pointer select-none items-center rounded-sm px-3 py-2 text-sm outline-none',
        'transition-colors',
        danger
          ? 'text-danger focus:bg-danger-subtle'
          : 'text-on-surface focus:bg-surface-elevated',
        className,
      )}
      {...props}
    />
  )
}

/* ── Separator ── */
function Separator({ className, ...props }: ComponentProps<typeof DropdownMenuPrimitive.Separator>) {
  return (
    <DropdownMenuPrimitive.Separator
      className={cn('my-1 h-px bg-border', className)}
      {...props}
    />
  )
}

/* ── Root re-export for composition ── */
const DropdownMenu = DropdownMenuPrimitive.Root

export { DropdownMenu, Trigger, Content, Item, Separator }
