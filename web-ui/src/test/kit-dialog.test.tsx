import { useState } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Modal } from '../components/ui/Modal'
import { ConfirmDialog } from '../components/ui/ConfirmDialog'

/**
 * Kit dialog tests — Radix Dialog behavioural verification.
 *
 * Radix portals content to document.body, so all queries use screen /
 * document.body rather than the render container, and waitFor absorbs
 * portal/focus timings (jsdom has no layout).
 */

/** External trigger + controlled Modal — proves focus return to the opener. */
function StatefulModal() {
  const [open, setOpen] = useState(false)
  return (
    <>
      <button type="button" onClick={() => setOpen(true)}>
        Open
      </button>
      <Modal open={open} onClose={() => setOpen(false)} title="Edit rule">
        <input aria-label="first field" />
        <input aria-label="second field" />
      </Modal>
    </>
  )
}

describe('Modal (Radix Dialog)', () => {
  it('renders nothing when open=false', () => {
    render(
      <Modal open={false} onClose={() => {}} title="Hidden">
        <p>Content</p>
      </Modal>,
    )
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('renders title and children when open', () => {
    render(
      <Modal open onClose={() => {}} title="Hello">
        <p>Body text</p>
      </Modal>,
    )
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText('Hello')).toBeInTheDocument()
    expect(screen.getByText('Body text')).toBeInTheDocument()
  })

  it('closes on Escape key', async () => {
    const onClose = vi.fn()
    render(
      <Modal open onClose={onClose} title="Escapable">
        <p>Press Escape</p>
      </Modal>,
    )
    await userEvent.keyboard('{Escape}')
    await waitFor(() => expect(onClose).toHaveBeenCalled())
  })

  it('closes on scrim (overlay) pointerdown', async () => {
    const onClose = vi.fn()
    render(
      <Modal open onClose={onClose} title="Scrim test">
        <p>Click outside</p>
      </Modal>,
    )
    // Radix Portal mounts Overlay and Content as siblings — the overlay is
    // the element rendered immediately before the dialog content.
    const dialog = await screen.findByRole('dialog')
    const overlay = dialog.previousElementSibling
    expect(overlay).not.toBeNull()
    fireEvent.pointerDown(overlay as Element)
    expect(onClose).toHaveBeenCalled()
  })

  it('traps Tab within the dialog and returns focus to the trigger on close', async () => {
    const user = userEvent.setup()
    render(<StatefulModal />)
    const trigger = screen.getByRole('button', { name: 'Open' })
    await user.click(trigger)

    const dialog = await screen.findByRole('dialog')

    // Tab cycles stay inside the dialog — whichever tabbable has focus,
    // activeElement must remain a descendant of the content.
    for (let i = 0; i < 5; i++) {
      await user.tab()
      expect(dialog.contains(document.activeElement)).toBe(true)
    }

    await user.keyboard('{Escape}')
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })
    await waitFor(() => expect(trigger).toHaveFocus())
  })

  it('has correct aria wiring: role, aria-modal, aria-labelledby', () => {
    render(
      <Modal open onClose={() => {}} title="Aria test">
        <p>Content</p>
      </Modal>,
    )
    const dialog = screen.getByRole('dialog')
    expect(dialog).toHaveAttribute('aria-modal', 'true')
    expect(dialog.getAttribute('aria-labelledby')).toBeTruthy()
    const labelId = dialog.getAttribute('aria-labelledby')!
    const labelEl = document.getElementById(labelId)
    expect(labelEl).toHaveTextContent('Aria test')
  })
})

describe('ConfirmDialog (Radix Dialog)', () => {
  it('renders nothing when open=false', () => {
    render(
      <ConfirmDialog
        open={false}
        onClose={() => {}}
        onConfirm={() => {}}
        title="Confirm"
        message="Are you sure?"
      />,
    )
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('renders impact text when provided', () => {
    render(
      <ConfirmDialog
        open
        onClose={() => {}}
        onConfirm={() => {}}
        title="Delete"
        message="This cannot be undone."
        impact="3 firewall rules will be removed"
      />,
    )
    expect(screen.getByText('3 firewall rules will be removed')).toBeInTheDocument()
  })

  it('does not render impact when omitted', () => {
    render(
      <ConfirmDialog
        open
        onClose={() => {}}
        onConfirm={() => {}}
        title="Delete"
        message="Are you sure?"
      />,
    )
    const dialog = screen.getByRole('dialog')
    const paragraphs = dialog.querySelectorAll('p')
    // Message paragraph only — no impact paragraph.
    expect(paragraphs.length).toBe(1)
  })

  it('disables both buttons when loading', () => {
    render(
      <ConfirmDialog
        open
        onClose={() => {}}
        onConfirm={() => {}}
        title="Delete"
        message="Are you sure?"
        loading
      />,
    )
    const buttons = screen.getAllByRole('button')
    expect(buttons.length).toBe(2)
    buttons.forEach((btn) => {
      expect(btn).toBeDisabled()
    })
  })

  it('calls onConfirm when confirm button clicked', async () => {
    const onConfirm = vi.fn()
    render(
      <ConfirmDialog
        open
        onClose={() => {}}
        onConfirm={onConfirm}
        title="Delete"
        message="Are you sure?"
        confirmLabel="Yes, delete"
      />,
    )
    await userEvent.click(screen.getByRole('button', { name: 'Yes, delete' }))
    expect(onConfirm).toHaveBeenCalledOnce()
  })

  it('has correct aria wiring', () => {
    render(
      <ConfirmDialog
        open
        onClose={() => {}}
        onConfirm={() => {}}
        title="Confirm"
        message="Are you sure?"
      />,
    )
    const dialog = screen.getByRole('dialog')
    expect(dialog).toHaveAttribute('aria-modal', 'true')
    expect(dialog.getAttribute('aria-labelledby')).toBeTruthy()
    const labelId = dialog.getAttribute('aria-labelledby')!
    const labelEl = document.getElementById(labelId)
    expect(labelEl).toHaveTextContent('Confirm')
  })
})
