import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { getErrMsg } from '../lib/utils'

/* -------------------------------------------------------------------------- */
/*  sonner mock — sonner renders outside jsdom viewport; mock the module so   */
/*  our re-export passes through without crashing.                            */
/* -------------------------------------------------------------------------- */

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    warning: vi.fn(),
    loading: vi.fn(),
    dismiss: vi.fn(),
    message: vi.fn(),
    promise: vi.fn(),
    custom: vi.fn(),
  },
  Toaster: () => null,
}))

/* -------------------------------------------------------------------------- */
/*  (1) toast helper re-exported and callable                                 */
/* -------------------------------------------------------------------------- */

describe('toast re-export from Toaster', () => {
  it('exports toast.success that can be called without crashing', async () => {
    const { toast } = await import('../components/ui/Toaster')
    expect(() => toast.success('done')).not.toThrow()
  })
})

/* -------------------------------------------------------------------------- */
/*  (2) Toaster component renders                                             */
/* -------------------------------------------------------------------------- */

describe('Toaster component', () => {
  it('renders without crashing (sonner mocked to null)', async () => {
    // jsdom lacks matchMedia — provide a minimal stub
    if (!window.matchMedia) {
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: (query: string) => ({
          matches: false,
          media: query,
          onchange: null,
          addListener: vi.fn(),
          removeListener: vi.fn(),
          addEventListener: vi.fn(),
          removeEventListener: vi.fn(),
          dispatchEvent: vi.fn(),
        }),
      })
    }
    const { Toaster } = await import('../components/ui/Toaster')
    const { container } = render(<Toaster />)
    expect(container).toBeTruthy()
  })
})

/* -------------------------------------------------------------------------- */
/*  (3) Skeleton renders with animate-pulse class                             */
/* -------------------------------------------------------------------------- */

describe('Skeleton', () => {
  it('renders a div with animate-pulse and bg-surface-elevated', async () => {
    const { Skeleton } = await import('../components/ui/Skeleton')
    const { container } = render(<Skeleton className="h-4 w-32" />)
    const el = container.firstChild as HTMLElement
    expect(el).toHaveClass('animate-pulse')
    expect(el).toHaveClass('bg-surface-elevated')
    expect(el).toHaveClass('h-4')
    expect(el).toHaveClass('w-32')
  })
})

/* -------------------------------------------------------------------------- */
/*  (4) QueryError renders title + message + Retry button                     */
/* -------------------------------------------------------------------------- */

describe('QueryError', () => {
  it('renders title, message, and Retry button; clicking Retry calls onRetry', async () => {
    const { QueryError } = await import('../components/ui/QueryError')
    const onRetry = vi.fn()
    const user = userEvent.setup()

    render(
      <QueryError
        title="Connection failed"
        message="Could not reach the server"
        onRetry={onRetry}
      />,
    )

    expect(screen.getByText('Connection failed')).toBeInTheDocument()
    expect(screen.getByText('Could not reach the server')).toBeInTheDocument()

    const retryBtn = screen.getByRole('button', { name: /retry/i })
    expect(retryBtn).toBeInTheDocument()

    await user.click(retryBtn)
    expect(onRetry).toHaveBeenCalledOnce()
  })

  it('renders no Retry button when onRetry is not provided', async () => {
    const { QueryError } = await import('../components/ui/QueryError')

    render(<QueryError title="Oops" message="Something broke" />)

    expect(screen.getByText('Oops')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /retry/i })).not.toBeInTheDocument()
  })
})

/* -------------------------------------------------------------------------- */
/*  (5) PageSkeleton renders skeleton primitives                              */
/* -------------------------------------------------------------------------- */

describe('PageSkeleton', () => {
  it('renders multiple elements with animate-pulse class', async () => {
    const { PageSkeleton } = await import('../components/ui/LoadingSpinner')
    const { container } = render(<PageSkeleton />)

    const skeletons = container.querySelectorAll('.animate-pulse')
    expect(skeletons.length).toBeGreaterThanOrEqual(5) // header(2) + 3 rows × 2 each = 8 minimum
  })
})

/* -------------------------------------------------------------------------- */
/*  (6) getErrMsg helper                                                      */
/* -------------------------------------------------------------------------- */

describe('getErrMsg', () => {
  it('extracts detail from axios-like error', () => {
    const err = { response: { data: { detail: 'Forbidden' } } }
    expect(getErrMsg(err)).toBe('Forbidden')
  })

  it('returns err.message for Error instances', () => {
    expect(getErrMsg(new Error('boom'))).toBe('boom')
  })

  it('returns string as-is', () => {
    expect(getErrMsg('raw string')).toBe('raw string')
  })

  it('falls back for null', () => {
    expect(getErrMsg(null)).toBe('An unexpected error occurred')
  })

  it('falls back for undefined', () => {
    expect(getErrMsg(undefined)).toBe('An unexpected error occurred')
  })

  it('falls back for plain object without response', () => {
    expect(getErrMsg({ foo: 'bar' })).toBe('An unexpected error occurred')
  })

  it('falls back for object with response but no data', () => {
    expect(getErrMsg({ response: {} })).toBe('An unexpected error occurred')
  })
})
