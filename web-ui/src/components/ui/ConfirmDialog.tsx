import { useRef } from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import { AlertTriangle } from 'lucide-react'
import { cn } from '../../lib/utils'

interface ConfirmDialogProps {
  open: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  message: string
  confirmLabel?: string
  loading?: boolean
  variant?: 'danger' | 'warning'
  /** Optional secondary line under `message` describing the blast radius. */
  impact?: string
}

/**
 * Destructive/uncertain-action confirmation on Radix Dialog.
 *
 * Gains vs the hand-rolled version: focus trap, Escape close, body-scroll
 * lock, role="dialog"/aria-modal, focus return to the opener. Same prop
 * contract plus the optional `impact` line. Scrim click still closes via the
 * explicit Overlay onPointerDown. Focus return mirrors Modal (see its docs).
 */
export function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel = 'Delete',
  loading = false,
  variant = 'danger',
  impact,
}: ConfirmDialogProps) {
  const isDanger = variant === 'danger'
  const lastFocusedRef = useRef<HTMLElement | null>(null)

  return (
    <Dialog.Root
      open={open}
      onOpenChange={(nextOpen) => {
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
            'w-full max-w-md mx-4',
            'bg-surface-card text-on-surface border border-border rounded-card shadow-xl',
            'focus:outline-none',
          )}
        >
          <div className="p-6">
            <div className="flex items-start gap-4">
              <div
                className={cn(
                  'p-2 rounded-full shrink-0',
                  isDanger ? 'bg-danger-subtle' : 'bg-warning-subtle',
                )}
              >
                <AlertTriangle
                  className={cn(
                    'w-6 h-6',
                    isDanger ? 'text-danger' : 'text-warning',
                  )}
                />
              </div>
              <div className="flex-1">
                <Dialog.Title className="text-lg font-semibold text-on-surface">
                  {title}
                </Dialog.Title>
                <Dialog.Description className="text-on-surface-muted mt-2">
                  {message}
                </Dialog.Description>
                {impact && (
                  <p className="text-on-surface-muted text-sm mt-1">{impact}</p>
                )}
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={onClose}
                disabled={loading}
                className="px-4 py-2 text-on-surface-muted bg-surface-elevated border border-border rounded-lg hover:text-on-surface hover:bg-surface disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={onConfirm}
                disabled={loading}
                className={cn(
                  'px-4 py-2 rounded-lg disabled:opacity-50',
                  isDanger
                    ? 'bg-danger text-danger-fg hover:bg-danger/90'
                    : 'bg-warning text-warning-fg hover:bg-warning/90',
                )}
              >
                {loading ? '...' : confirmLabel}
              </button>
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
