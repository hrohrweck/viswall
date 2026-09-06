import { useState, useMemo, type ReactNode } from 'react'
import {
  useLegacyTable as useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  type LegacyReactTable,
} from '@tanstack/react-table/legacy'
import {   flexRender, type SortingState, type PaginationState, type RowData, type ColumnSort } from '@tanstack/react-table'
import { ChevronUp, ChevronDown, ChevronsUpDown, ChevronLeft, ChevronRight, Search } from 'lucide-react'
import { Input } from './Input'
import { Skeleton } from './Skeleton'
import { QueryError } from './QueryError'

/* -------------------------------------------------------------------------- */
/*  Public types (PRESERVED — no breaking changes)                             */
/* -------------------------------------------------------------------------- */

export interface Column<T> {
  key: string
  header: string
  render?: (item: T) => ReactNode
  className?: string
}

export interface DataTableProps<T> {
  columns: Column<T>[]
  data: T[]
  keyExtractor: (item: T) => string | number
  onRowClick?: (item: T) => void
  emptyContent?: ReactNode
  /** Show sort chevrons in header; toggles asc/desc on click. */
  enableSorting?: boolean
  /** Render a search Input above the table that filters rows by global string match. */
  searchable?: boolean
  /** Placeholder for the search input. */
  searchPlaceholder?: string
  /** Enable built-in pagination footer. `true` uses default page size (10); object allows override. */
  pagination?: boolean | { pageSize?: number }
  /** Render an extra rightmost column with per-row actions (e.g. kebab menu). */
  rowActions?: (item: T) => ReactNode
  /** Show skeleton loading rows instead of data. */
  isLoading?: boolean
  /** Show error state with retry button. */
  isError?: boolean
  /** Called when the user clicks "Retry" in error state. */
  onRetry?: () => void
}

/* -------------------------------------------------------------------------- */
/*  DataTable                                                                  */
/* -------------------------------------------------------------------------- */

export function DataTable<T extends RowData>({
  columns,
  data,
  keyExtractor,
  onRowClick,
  emptyContent,
  enableSorting = false,
  searchable = false,
  searchPlaceholder = 'Search…',
  pagination: paginationProp,
  rowActions,
  isLoading = false,
  isError = false,
  onRetry,
}: DataTableProps<T>) {
  /* ── Local state for opt-in features ── */
  const [sorting, setSorting] = useState<SortingState>([])
  const [globalFilter, setGlobalFilter] = useState('')

  const pageSize = typeof paginationProp === 'object'
    ? (paginationProp.pageSize ?? 10)
    : 10
  const [pagination, setPagination] = useState<PaginationState>({
    pageIndex: 0,
    pageSize,
  })

  /* ── Map Column<T> → TanStack ColumnDef ── */
  const tanstackColumns = useMemo(
    () =>
      columns.map((c) => ({
        id: c.key,
        header: c.header,
        accessorFn: (row: T) => (row as Record<string, unknown>)[c.key],
        cell: (info: { getValue: () => unknown; row: { original: T } }) =>
          c.render ? c.render(info.row.original) : String(info.getValue() ?? ''),
      })),
    [columns],
  )

  /* ── Append row-actions column when slot provided ── */
  const allColumns = useMemo(() => {
    if (!rowActions) return tanstackColumns
    return [
      ...tanstackColumns,
      {
        id: '__rowActions',
        header: '',
        accessorFn: () => null as unknown,
        cell: (info: { row: { original: T } }) => rowActions(info.row.original),
      },
    ]
  }, [tanstackColumns, rowActions])

  /* ── TanStack table instance (v9 legacy compat: v8-style API) ── */
  const table: LegacyReactTable<T> = useReactTable({
    data,
    columns: allColumns as Parameters<typeof useReactTable<T>>[0]['columns'],
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: enableSorting ? getSortedRowModel() : undefined,
    getFilteredRowModel: searchable ? getFilteredRowModel() : undefined,
    getPaginationRowModel: paginationProp ? getPaginationRowModel() : undefined,
    state: {
      sorting: enableSorting ? sorting : [],
      globalFilter: searchable ? globalFilter : '',
      pagination: paginationProp ? pagination : undefined,
    },
    onSortingChange: enableSorting ? setSorting : undefined,
    onGlobalFilterChange: searchable ? setGlobalFilter : undefined,
    onPaginationChange: paginationProp ? setPagination : undefined,
    globalFilterFn: 'includesString',
    enableSorting,
    autoResetPageIndex: false,
  } as Parameters<typeof useReactTable<T>>[0])

  /* ── Built-in empty state (lite) ── */
  const defaultEmpty = (
    <div className="flex flex-col items-center justify-center py-12 text-center" data-testid="empty-state">
      <Search className="h-10 w-10 text-on-surface-muted mb-3" />
      <p className="text-sm text-on-surface-muted">No results</p>
    </div>
  )

  /* ── Error state ── */
  if (isError) {
    return (
      <div className="rounded-card border border-border bg-surface-card overflow-hidden">
        <QueryError onRetry={onRetry} />
      </div>
    )
  }

  /* ── Loading state ── */
  if (isLoading) {
    return (
      <div className="rounded-card border border-border bg-surface-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-surface-elevated">
                {columns.map((col) => (
                  <th
                    key={col.key}
                    className={`px-4 py-3 text-left text-xs font-medium text-on-surface-muted uppercase ${col.className ?? ''}`}
                  >
                    {col.header}
                  </th>
                ))}
                {rowActions && <th className="px-4 py-3" />}
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {Array.from({ length: 5 }, (_, i) => (
                <tr key={i}>
                  {columns.map((col) => (
                    <td key={col.key} className="px-4 py-3">
                      <Skeleton className="h-4 w-3/4" />
                    </td>
                  ))}
                  {rowActions && (
                    <td className="px-4 py-3">
                      <Skeleton className="h-4 w-8" />
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    )
  }

  /* ── Empty data (after loading/error guards; emptyContent takes precedence) ── */
  if (data.length === 0) {
    return (
      <div className="rounded-card border border-border bg-surface-card overflow-hidden">
        {emptyContent ?? defaultEmpty}
      </div>
    )
  }

  /* ── Rows to render ── */
  const rows = table.getRowModel().rows

  /* ── Sort icon helper ── */
  const sortIcon = (columnId: string) => {
    const sort = sorting.find((s: ColumnSort) => s.id === columnId)
    if (!sort) return <ChevronsUpDown className="h-3.5 w-3.5 opacity-40" />
    return sort.desc ? (
      <ChevronDown className="h-3.5 w-3.5" />
    ) : (
      <ChevronUp className="h-3.5 w-3.5" />
    )
  }

  /* ── Pagination helpers ── */
  const totalRows = table.getFilteredRowModel().rows.length
  const firstRow = pagination.pageIndex * pagination.pageSize + 1
  const lastRow = Math.min(firstRow + pagination.pageSize - 1, totalRows)

  return (
    <div className="rounded-card border border-border bg-surface-card overflow-hidden">
      {/* ── Search toolbar ── */}
      {searchable && (
        <div className="px-4 py-3 border-b border-border">
          <Input
            value={globalFilter}
            onChange={(e) => setGlobalFilter(e.target.value)}
            placeholder={searchPlaceholder}
            className="max-w-sm"
            aria-label="Search"
          />
        </div>
      )}

      {/* ── Table ── */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id} className="bg-surface-elevated">
                {headerGroup.headers.map((header) => {
                  const colMeta = columns.find((c) => c.key === header.id)
                  const isActionsCol = header.id === '__rowActions'
                  return (
                    <th
                      key={header.id}
                      className={`px-4 py-3 text-left text-xs font-medium text-on-surface-muted uppercase ${
                        colMeta?.className ?? ''
                      }`}
                    >
                      {enableSorting && !isActionsCol ? (
                        <button
                          type="button"
                          className="inline-flex items-center gap-1 hover:text-on-surface transition-colors"
                          onClick={header.column.getToggleSortingHandler()}
                        >
                          {flexRender(header.column.columnDef.header, header.getContext())}
                          {sortIcon(header.id)}
                        </button>
                      ) : (
                        flexRender(header.column.columnDef.header, header.getContext())
                      )}
                    </th>
                  )
                })}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-border">
            {rows.length === 0 && searchable ? (
              <tr>
                <td colSpan={allColumns.length}>
                  {emptyContent ?? defaultEmpty}
                </td>
              </tr>
            ) : (
              rows.map((row) => (
                <tr
                  key={keyExtractor(row.original)}
                  onClick={() => onRowClick?.(row.original)}
                  tabIndex={onRowClick ? 0 : undefined}
                  onKeyDown={
                    onRowClick
                      ? (e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault()
                            onRowClick(row.original)
                          }
                        }
                      : undefined
                  }
                  className={`hover:bg-surface-elevated/60 transition-colors ${
                    onRowClick
                      ? 'cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-primary'
                      : ''
                  }`}
                >
                  {row.getVisibleCells().map((cell) => {
                    const colMeta = columns.find((c) => c.key === cell.column.id)
                    return (
                      <td
                        key={cell.id}
                        className={`px-4 py-3 text-sm text-on-surface ${colMeta?.className ?? ''}`}
                      >
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    )
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* ── Pagination footer ── */}
      {paginationProp && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-border">
          <div className="flex items-center gap-2 text-sm text-on-surface-muted">
            <span>Rows per page</span>
            <select
              value={pagination.pageSize}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                setPagination((prev: PaginationState) => ({
                  ...prev,
                  pageSize: Number(e.target.value),
                  pageIndex: 0,
                }))
              }
              className="h-7 rounded border border-border bg-surface-card px-1.5 text-sm text-on-surface"
            >
              {[10, 25, 50].map((size) => (
                <option key={size} value={size}>
                  {size}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-4 text-sm text-on-surface-muted">
            <span>
              {totalRows === 0 ? '0' : `${firstRow}–${lastRow}`} of {totalRows}
            </span>
            <div className="flex gap-1">
              <button
                type="button"
                onClick={() => table.previousPage()}
                disabled={!table.getCanPreviousPage()}
                className="inline-flex items-center justify-center w-7 h-7 rounded border border-border hover:bg-surface-elevated disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                aria-label="Previous page"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={() => table.nextPage()}
                disabled={!table.getCanNextPage()}
                className="inline-flex items-center justify-center w-7 h-7 rounded border border-border hover:bg-surface-elevated disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                aria-label="Next page"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/*  Pagination (PRESERVED — kept for back-compat, zero external consumers)     */
/* -------------------------------------------------------------------------- */

export function Pagination({
  page,
  totalPages,
  onPageChange,
}: {
  page: number
  totalPages: number
  onPageChange: (page: number) => void
}) {
  if (totalPages <= 1) return null

  return (
    <div className="flex items-center justify-between px-6 py-3 border-t border-gray-200">
      <p className="text-sm text-gray-600">
        Page {page} of {totalPages}
      </p>
      <div className="flex gap-2">
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className="px-3 py-1 text-sm border rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Previous
        </button>
        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          className="px-3 py-1 text-sm border rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Next
        </button>
      </div>
    </div>
  )
}
