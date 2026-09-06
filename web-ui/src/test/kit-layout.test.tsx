import { describe, expect, it } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { Card } from '../components/ui/Card'
import { PageHeader } from '../components/ui/PageHeader'
import { Tabs, TabsContent } from '../components/ui/Tabs'
import { Breadcrumbs } from '../components/ui/Breadcrumbs'

/* -------------------------------------------------------------------------- */
/*  Kit layout tests — Card, PageHeader, Tabs, Breadcrumbs contract proofs    */
/* -------------------------------------------------------------------------- */

/* ---- 1. Card ------------------------------------------------------------- */

describe('Card', () => {
  it('renders title, actions, and body', () => {
    render(
      <Card
        title="Firewall Rules"
        actions={<button>Add rule</button>}
      >
        <p>Body content here</p>
      </Card>,
    )
    expect(screen.getByText('Firewall Rules')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Add rule' })).toBeInTheDocument()
    expect(screen.getByText('Body content here')).toBeInTheDocument()
  })

  it('does NOT render header when title and actions are omitted', () => {
    const { container } = render(
      <Card>
        <p>Just a body</p>
      </Card>,
    )
    // No h3 heading inside the card
    expect(container.querySelector('h3')).toBeNull()
    expect(screen.getByText('Just a body')).toBeInTheDocument()
  })
})

/* ---- 2. PageHeader — primary-action-last contract ------------------------ */

describe('PageHeader', () => {
  it('renders secondaryActions BEFORE primaryAction in DOM order', () => {
    render(
      <PageHeader
        title="Instances"
        description="Manage your edge nodes"
        primaryAction={<button>Deploy</button>}
        secondaryActions={[
          <button key="filter">Filter</button>,
          <button key="export">Export</button>,
        ]}
      />,
    )

    // Query all buttons in the action area — the DOM order must be:
    // Filter, Export (secondary), Deploy (primary — last)
    const buttons = screen.getAllByRole('button')
    const labels = buttons.map((b) => b.textContent)

    // Find the indices
    const filterIdx = labels.indexOf('Filter')
    const exportIdx = labels.indexOf('Export')
    const deployIdx = labels.indexOf('Deploy')

    expect(filterIdx).toBeGreaterThanOrEqual(0)
    expect(exportIdx).toBeGreaterThanOrEqual(0)
    expect(deployIdx).toBeGreaterThanOrEqual(0)

    // PRIMARY action (Deploy) must appear AFTER all secondary actions
    expect(deployIdx).toBeGreaterThan(filterIdx)
    expect(deployIdx).toBeGreaterThan(exportIdx)
  })

  it('renders tabs in a bordered strip below the header', () => {
    render(
      <PageHeader
        title="Mail"
        tabs={<div data-testid="tab-strip">Tab content</div>}
      />,
    )
    const tabStrip = screen.getByTestId('tab-strip')
    // The parent of the tab strip should have the border-b class
    expect(tabStrip.parentElement).toHaveClass('border-b')
  })
})

/* ---- 3. Tabs -------------------------------------------------------------- */

describe('Tabs', () => {
  it('clicking a tab switches the visible panel and sets aria-selected', async () => {
    const user = userEvent.setup()
    render(
      <Tabs
        items={[
          { value: 'overview', label: 'Overview' },
          { value: 'rules', label: 'Rules' },
        ]}
        defaultValue="overview"
      >
        <TabsContent value="overview">Overview panel</TabsContent>
        <TabsContent value="rules">Rules panel</TabsContent>
      </Tabs>,
    )

    // Default: overview panel visible
    expect(screen.getByText('Overview panel')).toBeInTheDocument()
    const rulesTab = screen.getByRole('tab', { name: 'Rules' })
    expect(rulesTab).toHaveAttribute('aria-selected', 'false')

    // Click the Rules tab — userEvent fires the full pointer + click sequence
    await user.click(rulesTab)

    // Wait for Radix to update the panel state
    await waitFor(() => {
      expect(screen.getByText('Rules panel')).toBeInTheDocument()
    })
    expect(rulesTab).toHaveAttribute('aria-selected', 'true')
  })

  it('arrow Right moves focus and selection', async () => {
    const user = userEvent.setup()
    render(
      <Tabs
        items={[
          { value: 'a', label: 'Tab A' },
          { value: 'b', label: 'Tab B' },
          { value: 'c', label: 'Tab C' },
        ]}
        defaultValue="a"
      >
        <TabsContent value="a">Panel A</TabsContent>
        <TabsContent value="b">Panel B</TabsContent>
        <TabsContent value="c">Panel C</TabsContent>
      </Tabs>,
    )

    const tabA = screen.getByRole('tab', { name: 'Tab A' })
    const tabB = screen.getByRole('tab', { name: 'Tab B' })

    // Focus the first tab
    tabA.focus()
    expect(tabA).toHaveFocus()

    // Press ArrowRight — userEvent triggers proper keyboard + focus sequence
    await user.keyboard('{ArrowRight}')

    // Radix roving tabindex: Tab B now has focus and is selected
    await waitFor(() => {
      expect(tabB).toHaveFocus()
    })
    expect(tabB).toHaveAttribute('aria-selected', 'true')
  })
})

/* ---- 4. Breadcrumbs ------------------------------------------------------- */

describe('Breadcrumbs', () => {
  it('renders nav aria-label, last item aria-current="page", and react-router Links', () => {
    render(
      <MemoryRouter>
        <Breadcrumbs
          items={[
            { label: 'Home', to: '/' },
            { label: 'Instances', to: '/instances' },
            { label: 'Berlin-01' },
          ]}
        />
      </MemoryRouter>,
    )

    // nav with aria-label
    const nav = screen.getByRole('navigation', { name: 'Breadcrumb' })
    expect(nav).toBeInTheDocument()

    // Last item: aria-current="page"
    const lastItem = screen.getByText('Berlin-01')
    expect(lastItem).toHaveAttribute('aria-current', 'page')

    // Links for items with `to` — react-router Link renders <a> elements
    const homeLink = screen.getByRole('link', { name: 'Home' })
    expect(homeLink).toHaveAttribute('href', '/')

    const instancesLink = screen.getByRole('link', { name: 'Instances' })
    expect(instancesLink).toHaveAttribute('href', '/instances')
  })

  it('renders nothing for empty items array', () => {
    const { container } = render(
      <MemoryRouter>
        <Breadcrumbs items={[]} />
      </MemoryRouter>,
    )
    expect(container.innerHTML).toBe('')
  })
})
