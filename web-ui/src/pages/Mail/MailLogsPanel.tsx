import { useEffect, useMemo, useRef, useState } from 'react'
import { Input, Button, QueryError } from '../../components/ui'
import { useMailLogs } from '../../hooks/useApi'
import type { MailLogsFilters } from '../../types'

const DEBOUNCE_MS = 400

/**
 * datetime-local values ("YYYY-MM-DDTHH:MM") are sent naive ("YYYY-MM-DD HH:MM")
 * with NO timezone conversion: exim writes agent-local wall-clock time, so
 * since/until are interpreted in the agent's local timezone, not the browser's.
 */
function toNaiveStamp(value: string): string {
  return value.replace('T', ' ')
}

interface MailLogsPanelProps {
  instanceId: number
  /** Hosted domain names, fed into the domain filter datalist. */
  domains: string[]
}

export function MailLogsPanel({ instanceId, domains }: MailLogsPanelProps) {
  const [qInput, setQInput] = useState('')
  const [domainInput, setDomainInput] = useState('')
  const [mailIdInput, setMailIdInput] = useState('')
  const [sinceInput, setSinceInput] = useState('')
  const [untilInput, setUntilInput] = useState('')
  const [filters, setFilters] = useState<MailLogsFilters>({})

  // Debounced filter state — changes produce a new queryKey, which resets the
  // infinite query to offset 0 with no manual cache surgery.
  useEffect(() => {
    const t = setTimeout(() => {
      setFilters({
        q: qInput || undefined,
        domain: domainInput || undefined,
        mail_id: mailIdInput || undefined,
        since: sinceInput ? toNaiveStamp(sinceInput) : undefined,
        until: untilInput ? toNaiveStamp(untilInput) : undefined,
      })
    }, DEBOUNCE_MS)
    return () => clearTimeout(t)
  }, [qInput, domainInput, mailIdInput, sinceInput, untilInput])

  const logsQuery = useMailLogs(instanceId, filters, true)
  const { hasNextPage, isFetchingNextPage, fetchNextPage } = logsQuery

  const lines = useMemo(
    () => logsQuery.data?.pages.flatMap((page) => page.lines) ?? [],
    [logsQuery.data],
  )
  const totalMatched = logsQuery.data?.pages[0]?.total_matched ?? 0
  const lastPage = logsQuery.data?.pages[logsQuery.data.pages.length - 1]
  const atEnd = logsQuery.data != null && (lastPage?.next_offset ?? null) === null

  const sentinelRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const el = sentinelRef.current
    if (!el) return
    const io = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting) && hasNextPage && !isFetchingNextPage) {
          void fetchNextPage()
        }
      },
      { rootMargin: '200px' },
    )
    io.observe(el)
    return () => io.disconnect()
  }, [hasNextPage, isFetchingNextPage, fetchNextPage])

  const hasActiveInputs = Boolean(
    qInput || domainInput || mailIdInput || sinceInput || untilInput,
  )

  const clearFilters = () => {
    setQInput('')
    setDomainInput('')
    setMailIdInput('')
    setSinceInput('')
    setUntilInput('')
  }

  return (
    <div className="flex flex-col h-[calc(100vh-15rem)] min-w-0">
      {/* Filter bar */}
      <div className="shrink-0 flex flex-wrap items-center gap-2 gap-y-3 pb-3 border-b border-border [contain:inline-size]">
        <Input
          aria-label="Keyword"
          placeholder="Keyword…"
          className="min-w-[10rem] grow basis-48"
          value={qInput}
          onChange={(e) => setQInput(e.target.value)}
        />
        <div className="min-w-[10rem] grow basis-48">
          <Input
            aria-label="Domain"
            list="mail-logs-domains"
            placeholder="Domain…"
            value={domainInput}
            onChange={(e) => setDomainInput(e.target.value)}
          />
          <datalist id="mail-logs-domains">
            {domains.map((d) => (
              <option key={d} value={d} />
            ))}
          </datalist>
        </div>
        <Input
          aria-label="Mail ID"
          placeholder="Mail ID…"
          mono
          className="min-w-[10rem] grow basis-48"
          value={mailIdInput}
          onChange={(e) => setMailIdInput(e.target.value)}
        />
        <Input
          aria-label="Since"
          type="datetime-local"
          className="min-w-[11rem] grow basis-48"
          value={sinceInput}
          onChange={(e) => setSinceInput(e.target.value)}
        />
        <Input
          aria-label="Until"
          type="datetime-local"
          className="min-w-[11rem] grow basis-48"
          value={untilInput}
          onChange={(e) => setUntilInput(e.target.value)}
        />
        <Button variant="secondary" disabled={!hasActiveInputs} onClick={clearFilters}>
          Clear Filters
        </Button>
      </div>

      {logsQuery.isError ? (
        <QueryError
          title="Log agent unreachable"
          onRetry={() => void logsQuery.refetch()}
        />
      ) : (
        <>
          <div className="flex-1 min-h-0 min-w-0 overflow-y-auto overflow-x-auto mt-3 [contain:inline-size]">
            {lines.map((line, i) => (
              <div
                key={i}
                className="font-mono text-xs whitespace-pre text-on-surface"
              >
                {line}
              </div>
            ))}
            {logsQuery.isLoading && lines.length === 0 && (
              <div className="p-3 text-sm text-on-surface-muted">Loading…</div>
            )}
            <div ref={sentinelRef} data-testid="logs-sentinel" className="h-px" />
          </div>
          <div className="shrink-0 pt-2 flex items-center gap-3 text-xs text-on-surface-muted">
            <span>{totalMatched.toLocaleString()} lines matched</span>
            {logsQuery.isFetching && <span>Loading…</span>}
            {atEnd && !logsQuery.isFetching && <span>End of logs</span>}
          </div>
        </>
      )}
    </div>
  )
}
