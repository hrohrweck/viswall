import { ReactNode, useRef } from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import { X } from 'lucide-react'
import { cn } from '../../lib/utils'

interface ModalProps {
  open: boolean
  onClose: () => void
  title: string
  children: ReactNode
  size?: 'sm' | 'md' | 'lg' | 'xl'
}

const sizeClasses = {
  sm: 'max-w-md',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
}

/**
 * Modal dialog built on Radix Dialog (focus trap, Escape, body-scroll lock,
 * role="dialog" / aria-modal, labelled title).
 *
 * Prop contract is UNCHANGED from the hand-rolled version — every existing
 * call site keeps working. Newly gained behaviour: Escape closes, focus is
 * trapped and returned to the opener on close, body scroll is locked.
 *
 * Backdrop (scrim) click closes, as before — the Overlay's explicit
 * onPointerDown→onClose keeps the close wired (Radix defers outside-dismiss
 * to pointerup, which real clicks produce but jsdom/RTL may not dispatch).
 * onClose is idempotent (parent just sets open=false).
 *
 * Focus return: Radix restores focus to a rendered Dialog.Trigger, but these
 * dialogs are opened programmatically by external buttons — so we record
 * document.activeElement in onOpenAutoFocus (fires before Radix moves focus)
 * and restore it in onCloseAutoFocus. aria-modal is set explicitly: this
 * Radix version does not emit it (verified in dist).
 */
export function Modal({ open, onClose, title, children, size = 'md' }: ModalProps) {
  const lastFocusedRef = useRef<HTMLElement | null>(null)

  return (
    <Dialog.Root
      open={open}
      onOpenChange={(nextOpen) => {
        // Controlled: only honour close. open→true cannot happen without a
        // trigger, but ignore it defensively — the parent owns `open`.
        if (!nextOpen) onClose()
      }}
    >
      <Dialog.Portal>
        <Dialog.Overlay
          className="fixed inset-0 z-50 bg-black/50"
          onPointerDown={onClose}
        />
        <Dialog.Content
          aria-modal="true"
          onOpenAutoFocus={() => {
            lastFocusedRef.current = document.activeElement as HTMLElement | null
          }}
          onCloseAutoFocus={(event) => {
            event.preventDefault()
            lastFocusedRef.current?.focus()
          }}
          onPointerDownOutside={onClose}
          className={cn(
            'fixed left-1/2 top-1/2 z-50 -translate-x-1/2 -translate-y-1/2',
            'w-full mx-4 max-h-[90vh] flex flex-col',
            'bg-surface-card text-on-surface border border-border rounded-card shadow-xl',
            'focus:outline-none',
            sizeClasses[size],
          )}
        >
          <div className="flex items-center justify-between px-6 py-4 border-b border-border">
            <Dialog.Title className="text-lg font-semibold text-on-surface">
              {title}
            </Dialog.Title>
            <Dialog.Close asChild>
              <button
                aria-label="Close"
                className="p-1 rounded-lg text-on-surface-muted hover:text-on-surface hover:bg-surface-elevated"
              >
                <X className="w-5 h-5" />
              </button>
            </Dialog.Close>
          </div>
          <div className="px-6 py-4 overflow-y-auto flex-1">{children}</div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
