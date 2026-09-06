import { describe, expect, it, vi } from 'vitest'
import { render, screen, within, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DataTable, type Column } from '../components/ui/DataTable'
import { DropdownMenu, Trigger as DropdownMenuTrigger, Content as DropdownMenuContent, Item as DropdownMenuItem } from '../components/ui/DropdownMenu'

/* -------------------------------------------------------------------------- */
/*  Fixture data                                                               */
/* -------------------------------------------------------------------------- */

interface Row { id: number; name: string; age: number }

const cols: Column<Row>[] = [
  { key: 'name', header: 'Name' },
  { key: 'age', header: 'Age' },
]

function makeRows(n: number): Row[] {
  return Array.from({ length: n }, (_, i) => ({ id: i + 1, name: `User ${String(i + 1).padStart(2, '0')}`, age: 20 + i }))
}

/** Return only tbody data rows (exclude thead header row). */
function getDataRows(): HTMLElement[] {
  const allRows = screen.getAllByRole('row')
  return allRows.filter((r) => r.parentElement?.tagName === 'TBODY')
}

/* -------------------------------------------------------------------------- */
/*  1 — PARITY: 30 rows → all 30 rendered, no toolbar, no footer              */
/* -------------------------------------------------------------------------- */

describe('DataTable parity', () => {
  it('renders all 30 rows with minimal props — no toolbar, no footer', () => {
    const rows = makeRows(30)
    render(
      <DataTable columns={cols} data={rows} keyExtractor={(r) => String(r.id)} />,
    )
    // 30 data rows + 1 header row = 31 total rows
    const allRows = screen.getAllByRole('row')
    expect(allRows).toHaveLength(31)
    // Spot-check first and last
    expect(screen.getByText('User 01')).toBeInTheDocument()
    expect(screen.getByText('User 30')).toBeInTheDocument()
    // No search input
    expect(screen.queryByPlaceholderText('Search…')).not.toBeInTheDocument()
    // No pagination footer
    expect(screen.queryByText(/Rows per page/)).not.toBeInTheDocument()
  })

  /* -------------------------------------------------------------------- */
  /*  2 — PARITY: emptyContent rendered when data empty                    */
  /* -------------------------------------------------------------------- */

  it('renders emptyContent when data is empty', () => {
    render(
      <DataTable
        columns={cols}
        data={[]}
        keyExtractor={(r) => String(r.id)}
        emptyContent={<p>Nothing here</p>}
      />,
    )
    expect(screen.getByText('Nothing here')).toBeInTheDocument()
  })

  /* -------------------------------------------------------------------- */
  /*  3 — PARITY: built-in 'No results' when data empty + no emptyContent  */
  /* -------------------------------------------------------------------- */

  it('renders built-in "No results" when data is empty and no emptyContent', () => {
    render(
      <DataTable columns={cols} data={[]} keyExtractor={(r) => String(r.id)} />,
    )
    expect(screen.getByText('No results')).toBeInTheDocument()
  })
})

/* -------------------------------------------------------------------------- */
/*  4 — enableSorting: click header toggles order                             */
/* -------------------------------------------------------------------------- */

describe('DataTable enableSorting', () => {
  it('clicking header toggles sort order', async () => {
    const user = userEvent.setup()
    const rows: Row[] = [
      { id: 1, name: 'Charlie', age: 30 },
      { id: 2, name: 'Alice', age: 25 },
      { id: 3, name: 'Bob', age: 35 },
    ]
    render(
      <DataTable columns={cols} data={rows} keyExtractor={(r) => String(r.id)} enableSorting />,
    )

    const nameHeader = screen.getByRole('button', { name: /name/i })

    // Click → asc (default toggle goes to asc first)
    await user.click(nameHeader)
    await waitFor(() => {
      const dataRows = getDataRows()
      const firstRowText = dataRows[0]?.textContent ?? ''
      expect(firstRowText).toContain('Alice')
    })

    // Click again → desc
    await user.click(nameHeader)
    await waitFor(() => {
      const dataRows = getDataRows()
      const firstRowText = dataRows[0]?.textContent ?? ''
      expect(firstRowText).toContain('Charlie')
    })
  })
})

/* -------------------------------------------------------------------------- */
/*  5 — searchable: type filters rows, clear restores                         */
/* -------------------------------------------------------------------------- */

describe('DataTable searchable', () => {
  it('typing in search input filters rows; clearing restores all', async () => {
    const user = userEvent.setup()
    const rows = makeRows(5)
    render(
      <DataTable columns={cols} data={rows} keyExtractor={(r) => String(r.id)} searchable />,
    )

    const input = screen.getByPlaceholderText('Search…')
    // All 5 rows initially
    expect(screen.getByText('User 01')).toBeInTheDocument()
    expect(screen.getByText('User 05')).toBeInTheDocument()

    // Type filter
    await user.type(input, 'User 03')
    await waitFor(() => {
      expect(screen.getByText('User 03')).toBeInTheDocument()
      expect(screen.queryByText('User 01')).not.toBeInTheDocument()
    })

    // Clear filter
    await user.clear(input)
    await waitFor(() => {
      expect(screen.getByText('User 01')).toBeInTheDocument()
      expect(screen.getByText('User 05')).toBeInTheDocument()
    })
  })
})

/* -------------------------------------------------------------------------- */
/*  6 — pagination: pageSize 10, next/prev, page indicator                    */
/* -------------------------------------------------------------------------- */

describe('DataTable pagination', () => {
  it('shows 1–10 of 30, navigates pages, prev disabled on page 1', async () => {
    const user = userEvent.setup()
    const rows = makeRows(30)
    render(
      <DataTable columns={cols} data={rows} keyExtractor={(r) => String(r.id)} pagination={{ pageSize: 10 }} />,
    )

    // Footer shows "1–10 of 30"
    expect(screen.getByText('1–10 of 30')).toBeInTheDocument()

    // Prev disabled
    const prevBtn = screen.getByRole('button', { name: /previous page/i })
    expect(prevBtn).toBeDisabled()

    // Next → 11–20
    const nextBtn = screen.getByRole('button', { name: /next page/i })
    await user.click(nextBtn)
    await waitFor(() => {
      expect(screen.getByText('11–20 of 30')).toBeInTheDocument()
    })

    // Prev now enabled
    expect(prevBtn).not.toBeDisabled()

    // Prev → back to 1–10
    await user.click(prevBtn)
    await waitFor(() => {
      expect(screen.getByText('1–10 of 30')).toBeInTheDocument()
    })
  })
})

/* -------------------------------------------------------------------------- */
/*  7 — isLoading → skeleton rows, no data                                    */
/* -------------------------------------------------------------------------- */

describe('DataTable isLoading', () => {
  it('renders skeleton rows with animate-pulse, no data rows', () => {
    const rows = makeRows(5)
    render(
      <DataTable columns={cols} data={rows} keyExtractor={(r) => String(r.id)} isLoading />,
    )
    // Skeleton uses animate-pulse class
    const skeletons = document.querySelectorAll('.animate-pulse')
    // 5 rows × 2 cols = 10 skeleton cells
    expect(skeletons.length).toBeGreaterThanOrEqual(5)
    // No actual data visible
    expect(screen.queryByText('User 01')).not.toBeInTheDocument()
  })
})

/* -------------------------------------------------------------------------- */
/*  8 — isError → QueryError with Retry                                       */
/* -------------------------------------------------------------------------- */

describe('DataTable isError', () => {
  it('renders QueryError with Retry button; onRetry is called', async () => {
    const user = userEvent.setup()
    const onRetry = vi.fn()
    render(
      <DataTable
        columns={cols}
        data={[]}
        keyExtractor={(r) => String(r.id)}
        isError
        onRetry={onRetry}
      />,
    )
    // QueryError renders "Something went wrong"
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    // Retry button present
    const retryBtn = screen.getByRole('button', { name: /retry/i })
    expect(retryBtn).toBeInTheDocument()
    await user.click(retryBtn)
    expect(onRetry).toHaveBeenCalledOnce()
  })
})

/* -------------------------------------------------------------------------- */
/*  9 — rowActions → extra column renders slot content                        */
/* -------------------------------------------------------------------------- */

describe('DataTable rowActions', () => {
  it('renders an extra cell with rowActions content', () => {
    const rows: Row[] = [{ id: 1, name: 'Alice', age: 25 }]
    render(
      <DataTable
        columns={cols}
        data={rows}
        keyExtractor={(r) => String(r.id)}
        rowActions={(item) => <button data-testid={`action-${item.id}`}>Action</button>}
      />,
    )
    expect(screen.getByTestId('action-1')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Action' })).toBeInTheDocument()
  })

  it('rowActions with DropdownMenu: kebab opens menu and item is clickable', async () => {
    const user = userEvent.setup()
    const onEdit = vi.fn()
    const rows: Row[] = [{ id: 1, name: 'Alice', age: 25 }]
    render(
      <DataTable
        columns={cols}
        data={rows}
        keyExtractor={(r) => String(r.id)}
        rowActions={(item) => (
          <DropdownMenu>
            <DropdownMenuTrigger label="Actions" />
            <DropdownMenuContent>
              <DropdownMenuItem onClick={() => onEdit(item.id)}>Edit</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      />,
    )
    // Click kebab
    const trigger = screen.getByRole('button', { name: 'Actions' })
    await user.click(trigger)
    // Menu item appears
    await waitFor(() => {
      expect(screen.getByText('Edit')).toBeInTheDocument()
    })
    // Click menu item
    await user.click(screen.getByText('Edit'))
    expect(onEdit).toHaveBeenCalledWith(1)
  })
})

/* -------------------------------------------------------------------------- */
/*  10 — onRowClick keyboard: tabIndex=0 + Enter triggers click                */
/* -------------------------------------------------------------------------- */

describe('DataTable onRowClick keyboard', () => {
  it('data row has tabIndex=0 and Enter triggers onRowClick', async () => {
    const user = userEvent.setup()
    const onClick = vi.fn()
    const rows: Row[] = [{ id: 1, name: 'Alice', age: 25 }]
    render(
      <DataTable columns={cols} data={rows} keyExtractor={(r) => String(r.id)} onRowClick={onClick} />,
    )
    const dataRows = getDataRows()
    expect(dataRows).toHaveLength(1)
    const row = dataRows[0]
    expect(row).toHaveAttribute('tabindex', '0')
    row.focus()
    await user.keyboard('{Enter}')
    expect(onClick).toHaveBeenCalledWith(rows[0])
  })

  it('data row has no tabIndex when onRowClick is not set', () => {
    const rows: Row[] = [{ id: 1, name: 'Alice', age: 25 }]
    render(
      <DataTable columns={cols} data={rows} keyExtractor={(r) => String(r.id)} />,
    )
    const dataRows = getDataRows()
    expect(dataRows).toHaveLength(1)
    expect(dataRows[0]).not.toHaveAttribute('tabindex')
  })
})

/* -------------------------------------------------------------------------- */
/*  11 — pagination: pageSize select changes page size                        */
/* -------------------------------------------------------------------------- */

describe('DataTable pagination pageSize select', () => {
  it('changing pageSize select resets to page 1 and shows correct range', async () => {
    const user = userEvent.setup()
    const rows = makeRows(30)
    render(
      <DataTable columns={cols} data={rows} keyExtractor={(r) => String(r.id)} pagination={{ pageSize: 10 }} />,
    )
    expect(screen.getByText('1–10 of 30')).toBeInTheDocument()
    // Change to 25
    const select = screen.getByRole('combobox')
    await user.selectOptions(select, '25')
    await waitFor(() => {
      expect(screen.getByText('1–25 of 30')).toBeInTheDocument()
    })
  })
})
