import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { Server } from 'lucide-react'
import {
  Card,
  CardBody,
  CardHeader,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  EmptyState,
  InstanceSelector,
  LoadingSpinner,
  SkeletonText,
  Tooltip,
} from '../components/ui'
import { useInstances } from '../hooks/useApi'
import { useInstanceStore } from '../stores/instance'
import { InstanceStatus, type Instance } from '../types'

/* -------------------------------------------------------------------------- */
/*  Coverage gap-fill (task 29). These kit exports had ZERO behavioural       */
/*  coverage after the audit: SkeletonText, LoadingSpinner, EmptyState,       */
/*  InstanceSelector, Tooltip, DropdownMenuSeparator (+ Item danger variant)  */
/*  and the Card compound sub-components. Everything else is covered by       */
/*  kit-*.test.tsx / shell-*.test.tsx.                                        */
/* -------------------------------------------------------------------------- */

vi.mock('../hooks/useApi', () => ({
  useInstances: vi.fn(),
}))

const mockedUseInstances = vi.mocked(useInstances)

/* jsdom lacks matchMedia / ResizeObserver — defensive stubs for Radix
   internals (Tooltip's PopperContent uses ResizeObserver via useSize). */
beforeAll(() => {
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
  if (!('ResizeObserver' in globalThis)) {
    class ResizeObserverStub {
      observe = vi.fn()
      unobserve = vi.fn()
      disconnect = vi.fn()
    }
    Object.defineProperty(globalThis, 'ResizeObserver', {
      writable: true,
      value: ResizeObserverStub,
    })
  }
})

function mkInstance(overrides: Partial<Instance> = {}): Instance {
  return {
    id: 1,
    name: 'fw-core',
    hostname: 'fw-core.local',
    capabilities: ['firewall'],
    api_endpoint: 'https://fw-core.local:8443',
    status: InstanceStatus.ACTIVE,
    last_seen: null,
    config: {},
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

function mockInstances(data: Instance[] | undefined, isLoading = false) {
  mockedUseInstances.mockReturnValue({ data, isLoading } as ReturnType<typeof useInstances>)
}

beforeEach(() => {
  mockedUseInstances.mockReset()
  useInstanceStore.setState({ selectedInstanceId: null })
})

/* -------------------------------------------------------------------------- */
/*  (1) SkeletonText                                                          */
/* -------------------------------------------------------------------------- */

describe('SkeletonText', () => {
  it('renders the requested number of lines; all full-width except the last (w-2/3)', () => {
    const { container } = render(<SkeletonText lines={4} />)
    const wrapper = container.firstElementChild as HTMLElement
    expect(wrapper).toHaveClass('space-y-2')
    expect(wrapper.children).toHaveLength(4)
    const lines = Array.from(wrapper.children) as HTMLElement[]
    expect(lines[0]).toHaveClass('w-full', 'h-4')
    expect(lines[2]).toHaveClass('w-full')
    expect(lines[3]).toHaveClass('w-2/3', 'h-4')
  })

  it('defaults to 3 lines and passes className through to the wrapper', () => {
    const { container } = render(<SkeletonText className="mt-6" />)
    const wrapper = container.firstElementChild as HTMLElement
    expect(wrapper.children).toHaveLength(3)
    expect(wrapper).toHaveClass('mt-6')
  })
})

/* -------------------------------------------------------------------------- */
/*  (2) LoadingSpinner                                                        */
/* -------------------------------------------------------------------------- */

describe('LoadingSpinner', () => {
  it('renders a centered spinning ring and merges className', () => {
    const { container } = render(<LoadingSpinner className="min-h-40" />)
    const wrapper = container.firstElementChild as HTMLElement
    expect(wrapper).toHaveClass('flex', 'items-center', 'justify-center', 'py-12', 'min-h-40')
    const ring = wrapper.firstElementChild as HTMLElement
    expect(ring).toHaveClass('animate-spin', 'rounded-full', 'border-t-primary-600')
  })
})

/* -------------------------------------------------------------------------- */
/*  (3) EmptyState                                                            */
/* -------------------------------------------------------------------------- */

describe('EmptyState', () => {
  it('renders icon, title and description without any action by default', () => {
    const { container } = render(
      <EmptyState icon={Server} title="Nothing here" description="Pick an instance first." />,
    )
    expect(container.querySelector('svg')).toHaveClass('w-16')
    expect(screen.getByRole('heading', { level: 3, name: 'Nothing here' })).toBeInTheDocument()
    expect(screen.getByText('Pick an instance first.')).toBeInTheDocument()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })

  it('actionTo renders a router Link with the action label', () => {
    render(
      <MemoryRouter>
        <EmptyState
          icon={Server}
          title="No rules"
          description="Add your first rule."
          actionLabel="Add rule"
          actionTo="/firewall/new"
        />
      </MemoryRouter>,
    )
    const link = screen.getByRole('link', { name: 'Add rule' })
    expect(link).toHaveAttribute('href', '/firewall/new')
  })

  it('onAction renders a Button wired to the handler', async () => {
    const user = userEvent.setup()
    const onAction = vi.fn()
    render(
      <EmptyState
        icon={Server}
        title="No rules"
        description="Add your first rule."
        actionLabel="Add rule"
        onAction={onAction}
      />,
    )
    await user.click(screen.getByRole('button', { name: 'Add rule' }))
    expect(onAction).toHaveBeenCalledTimes(1)
  })
})

/* -------------------------------------------------------------------------- */
/*  (4) InstanceSelector                                                      */
/* -------------------------------------------------------------------------- */

describe('InstanceSelector', () => {
  it('shows a loading placeholder while instances load', () => {
    mockInstances(undefined, true)
    render(<InstanceSelector />)
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('shows a placeholder when no instances exist', () => {
    mockInstances([])
    render(<InstanceSelector />)
    expect(screen.getByText('No instances')).toBeInTheDocument()
  })

  it('opens on click, selects an instance into the store and closes', async () => {
    const user = userEvent.setup()
    mockInstances([mkInstance(), mkInstance({ id: 2, name: 'fw-edge', hostname: 'fw-edge.local' })])
    render(<InstanceSelector />)

    await user.click(screen.getByRole('button', { name: /Select instance/ }))
    expect(screen.getByText('fw-edge.local')).toBeInTheDocument()

    await user.click(screen.getByText('fw-edge'))
    expect(useInstanceStore.getState().selectedInstanceId).toBe(2)
    expect(screen.queryByText('fw-edge.local')).not.toBeInTheDocument()
  })

  it('closes the list on an outside mousedown', async () => {
    const user = userEvent.setup()
    mockInstances([mkInstance()])
    render(<InstanceSelector />)

    await user.click(screen.getByRole('button', { name: /Select instance/ }))
    expect(screen.getByText('fw-core.local')).toBeInTheDocument()

    fireEvent.mouseDown(document.body)
    expect(screen.queryByText('fw-core.local')).not.toBeInTheDocument()
  })

  it('shows the selected instance name on the trigger', () => {
    useInstanceStore.setState({ selectedInstanceId: 1 })
    mockInstances([mkInstance()])
    render(<InstanceSelector />)
    expect(screen.getByRole('button', { name: /fw-core/ })).toBeInTheDocument()
  })
})

/* -------------------------------------------------------------------------- */
/*  (5) Tooltip                                                               */
/* -------------------------------------------------------------------------- */

describe('Tooltip', () => {
  it('renders hidden by default and shows its content in a portal on hover', async () => {
    const user = userEvent.setup()
    render(
      <Tooltip content="Hello tip" delayDuration={0}>
        <button>Hover me</button>
      </Tooltip>,
    )
    expect(screen.queryByText('Hello tip')).not.toBeInTheDocument()

    await user.hover(screen.getByRole('button', { name: 'Hover me' }))
    expect(await screen.findByText('Hello tip')).toBeInTheDocument()
  })
})

/* -------------------------------------------------------------------------- */
/*  (6) DropdownMenu — Separator + danger Item (portal)                       */
/* -------------------------------------------------------------------------- */

describe('DropdownMenu separator and danger item', () => {
  it('renders a separator and a danger-styled item inside the menu portal', async () => {
    const user = userEvent.setup()
    const onEdit = vi.fn()
    const onDelete = vi.fn()
    render(
      <DropdownMenu>
        <DropdownMenuTrigger />
        <DropdownMenuContent>
          <DropdownMenuItem onClick={onEdit}>Edit</DropdownMenuItem>
          <DropdownMenuSeparator data-testid="menu-separator" />
          <DropdownMenuItem danger onClick={onDelete}>
            Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>,
    )

    await user.click(screen.getByRole('button', { name: 'Actions' }))

    const separator = await screen.findByTestId('menu-separator')
    expect(separator).toHaveClass('h-px', 'bg-border')
    expect(separator).toHaveAttribute('role', 'separator')

    /* Radix closes the menu on selection — assert danger styling while it is open. */
    expect(screen.getByText('Delete')).toHaveClass('text-danger')

    await user.click(screen.getByText('Edit'))
    expect(onEdit).toHaveBeenCalledTimes(1)

    /* The menu unmounts after a selection — reopen before clicking Delete. */
    await user.click(screen.getByRole('button', { name: 'Actions' }))
    await user.click(await screen.findByText('Delete'))
    expect(onDelete).toHaveBeenCalledTimes(1)
  })
})

/* -------------------------------------------------------------------------- */
/*  (7) Card compound sub-components                                          */
/* -------------------------------------------------------------------------- */

describe('Card compound sub-components', () => {
  it('CardHeader renders title (h3) left and actions right; CardBody honours padding override', () => {
    render(
      <Card>
        <CardHeader title="Net rules" actions={<button>Add</button>} />
        <CardBody padding="p-3">
          <p>Body content</p>
        </CardBody>
      </Card>,
    )
    const title = screen.getByRole('heading', { level: 3, name: 'Net rules' })
    expect(title).toBeInTheDocument()
    // header wraps the title and carries the bottom border
    expect(title.parentElement).toHaveClass('border-b')
    expect(title.parentElement).toContainElement(screen.getByRole('button', { name: 'Add' }))
    const body = screen.getByText('Body content').parentElement as HTMLElement
    expect(body).toHaveClass('p-3')
  })
})
