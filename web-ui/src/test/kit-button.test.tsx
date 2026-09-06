import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Save, Trash2 } from 'lucide-react'
import { Button, IconButton, buttonVariants } from '../components/ui/Button'

/**
 * Kit button tests — variant classes, loading/disabled behaviour,
 * icon rendering, and IconButton accessibility.
 */

/* -------------------------------------------------------------------------- */
/*  Button                                                                     */
/* -------------------------------------------------------------------------- */

describe('Button', () => {
  it('renders label text', () => {
    render(<Button>Save changes</Button>)
    expect(screen.getByRole('button', { name: 'Save changes' })).toBeInTheDocument()
  })

  it.each([
    ['primary', 'bg-primary'],
    ['secondary', 'bg-surface-card'],
    ['ghost', 'hover:bg-surface-elevated'],
    ['destructive', 'bg-danger'],
  ] as const)('variant=%s applies %s class', (variant, expectedClass) => {
    render(<Button variant={variant}>{variant}</Button>)
    expect(screen.getByRole('button')).toHaveClass(expectedClass)
  })

  it.each(['sm', 'md', 'lg'] as const)('size=%s applies correct height', (size) => {
    render(<Button size={size}>{size}</Button>)
    const btn = screen.getByRole('button')
    const expectedHeight = { sm: 'h-8', md: 'h-9', lg: 'h-10' }[size]
    expect(btn).toHaveClass(expectedHeight)
  })

  it('loading disables the button and shows spinner', () => {
    render(<Button loading>Submit</Button>)
    const btn = screen.getByRole('button', { name: /submit/i })
    expect(btn).toBeDisabled()
    // Loader2 renders an <svg> with class animate-spin
    const spinner = btn.querySelector('svg.animate-spin')
    expect(spinner).toBeInTheDocument()
    // Label is preserved
    expect(btn).toHaveTextContent('Submit')
  })

  it('click fires onClick when enabled', async () => {
    const onClick = vi.fn()
    render(<Button onClick={onClick}>Click me</Button>)
    await userEvent.click(screen.getByRole('button'))
    expect(onClick).toHaveBeenCalledOnce()
  })

  it('click does NOT fire onClick when disabled', async () => {
    const onClick = vi.fn()
    render(<Button disabled onClick={onClick}>Disabled</Button>)
    await userEvent.click(screen.getByRole('button'))
    expect(onClick).not.toHaveBeenCalled()
  })

  it('click does NOT fire onClick when loading', async () => {
    const onClick = vi.fn()
    render(<Button loading onClick={onClick}>Loading</Button>)
    await userEvent.click(screen.getByRole('button'))
    expect(onClick).not.toHaveBeenCalled()
  })

  it('renders a leading icon when icon prop is provided', () => {
    render(<Button icon={Save}>Save</Button>)
    const btn = screen.getByRole('button')
    // The Save icon renders as an <svg> — look for the Lucide icon wrapper
    const svgs = btn.querySelectorAll('svg')
    expect(svgs.length).toBeGreaterThanOrEqual(1)
  })

  it('has focus-visible ring classes', () => {
    render(<Button>Ring</Button>)
    const btn = screen.getByRole('button')
    expect(btn).toHaveClass('focus-visible:ring-2')
    expect(btn).toHaveClass('focus-visible:ring-primary')
    expect(btn).toHaveClass('focus-visible:ring-offset-surface')
  })

  it('spreads native button props', () => {
    render(<Button data-testid="custom" type="submit">Go</Button>)
    const btn = screen.getByTestId('custom')
    expect(btn).toHaveAttribute('type', 'submit')
  })
})

/* -------------------------------------------------------------------------- */
/*  buttonVariants (cva export for Link composition)                           */
/* -------------------------------------------------------------------------- */

describe('buttonVariants', () => {
  it('returns a class string for a given variant', () => {
    const cls = buttonVariants({ variant: 'destructive' })
    expect(cls).toContain('bg-danger')
  })
})

/* -------------------------------------------------------------------------- */
/*  IconButton                                                                 */
/* -------------------------------------------------------------------------- */

describe('IconButton', () => {
  it('renders with aria-label and icon', () => {
    render(<IconButton icon={Trash2} label="Delete item" />)
    const btn = screen.getByRole('button', { name: 'Delete item' })
    expect(btn).toBeInTheDocument()
    expect(btn).toHaveAttribute('aria-label', 'Delete item')
    // Icon SVG rendered
    expect(btn.querySelector('svg')).toBeInTheDocument()
  })

  it('applies ghost variant by default', () => {
    render(<IconButton icon={Trash2} label="Delete" />)
    const btn = screen.getByRole('button')
    // ghost = no bg color, has hover:bg-surface-elevated
    expect(btn.className).not.toContain('bg-primary')
    expect(btn.className).not.toContain('bg-danger')
  })

  it('applies secondary variant when specified', () => {
    render(<IconButton icon={Trash2} label="Delete" variant="secondary" />)
    const btn = screen.getByRole('button')
    expect(btn).toHaveClass('bg-surface-card')
    expect(btn).toHaveClass('border')
  })

  it('respects size prop for w/h', () => {
    render(<IconButton icon={Trash2} label="Delete" size="lg" />)
    const btn = screen.getByRole('button')
    expect(btn).toHaveClass('w-10')
    expect(btn).toHaveClass('h-10')
  })

  it('sets type="button" by default', () => {
    render(<IconButton icon={Trash2} label="Delete" />)
    expect(screen.getByRole('button')).toHaveAttribute('type', 'button')
  })

  it('spreads native button props', async () => {
    const onClick = vi.fn()
    render(<IconButton icon={Trash2} label="Delete" onClick={onClick} />)
    await userEvent.click(screen.getByRole('button'))
    expect(onClick).toHaveBeenCalledOnce()
  })
})
