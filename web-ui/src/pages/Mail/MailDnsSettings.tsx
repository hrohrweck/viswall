import { useState } from 'react'
import { CheckCircle2, XCircle, AlertTriangle, MinusCircle, Copy } from 'lucide-react'
import { useInstanceStore } from '../../stores/instance'
import { useMailDomainDnsRecords, useMailDnsCheck, useRegenerateDkim } from '../../hooks/useApi'
import { Badge, Button, Card, ConfirmDialog, QueryError, Skeleton, toast } from '../../components/ui'
import { getErrMsg } from '../../lib/utils'
import type { MailDomain, MailDnsCheckResponse, MailDnsRecordSpec } from '../../types'

interface MailDnsSettingsProps {
  domain: MailDomain
}

const CHECK_STATUS_VARIANT: Record<string, 'success' | 'danger' | 'warning' | 'neutral'> = {
  correct: 'success',
  incorrect: 'danger',
  missing: 'warning',
  error: 'neutral',
}

const CHECK_STATUS_ICON: Record<string, typeof CheckCircle2 | undefined> = {
  correct: CheckCircle2,
  incorrect: XCircle,
  missing: AlertTriangle,
  error: MinusCircle,
}

const CHECK_STATUS_LABEL: Record<string, string> = {
  correct: 'Correct',
  incorrect: 'Incorrect',
  missing: 'Missing',
  error: 'Error',
}

export function MailDnsSettings({ domain }: MailDnsSettingsProps) {
  const { selectedInstanceId } = useInstanceStore()
  const { data: dns, isLoading, isError, refetch } = useMailDomainDnsRecords(selectedInstanceId!, domain.id)
  const checkMutation = useMailDnsCheck(selectedInstanceId!, domain.id)
  const dkimMutation = useRegenerateDkim(selectedInstanceId!)

  const [lastCheck, setLastCheck] = useState<MailDnsCheckResponse | null>(null)
  const [showDkimConfirm, setShowDkimConfirm] = useState(false)

  const checkByKey = new Map((lastCheck?.results ?? []).map((result) => [result.key, result]))

  const handleCopy = async (value: string) => {
    await navigator.clipboard.writeText(value)
    toast.success('Copied to clipboard')
  }

  const handleCheck = async () => {
    try {
      const result = await checkMutation.mutateAsync()
      setLastCheck(result)
    } catch (e) {
      toast.error(getErrMsg(e))
    }
  }

  const handleDkimRegenerate = async () => {
    try {
      await dkimMutation.mutateAsync(domain.id)
      toast.success('DKIM key regenerated — update your DNS record')
      setShowDkimConfirm(false)
    } catch (e) {
      toast.error(getErrMsg(e))
    }
  }

  const renderStatus = (record: MailDnsRecordSpec) => {
    const result = checkByKey.get(record.key)
    if (!result) {
      return <Badge variant="neutral">Not checked</Badge>
    }
    const variant = CHECK_STATUS_VARIANT[result.status] ?? 'neutral'
    const Icon = CHECK_STATUS_ICON[result.status]
    return (
      <Badge variant={variant} icon={Icon}>
        {CHECK_STATUS_LABEL[result.status] ?? result.status}
      </Badge>
    )
  }

  if (isLoading) {
    return (
      <div className="mt-4 space-y-4">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-20 w-2/3" />
      </div>
    )
  }

  if (isError || !dns) {
    return (
      <div className="mt-4">
        <QueryError title="Could not load DNS records" message="Try again to fetch the DNS records for this domain." onRetry={() => refetch()} />
      </div>
    )
  }

  return (
    <div className="mt-4 space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <h3 className="text-lg font-semibold text-on-surface">DNS Settings</h3>
          <p className="text-sm text-on-surface-muted">
            DNS records this appliance expects you to publish; run a live check to verify.
          </p>
          {lastCheck && (
            <p className="text-sm text-on-surface-muted">
              Last checked: {new Date(lastCheck.checked_at).toLocaleString()}
            </p>
          )}
        </div>
        <Button onClick={handleCheck} loading={checkMutation.isPending}>
          Check DNS
        </Button>
      </div>

      <Card>
        <div className="divide-y divide-border">
          {dns.records.map((record) => {
            const result = checkByKey.get(record.key)
            const isNotGenerated = !!record.note && record.note.startsWith('not_generated')
            const extraNote = isNotGenerated && record.note
              ? record.note.slice('not_generated'.length).trim()
              : ''
            const noteVisible = !!record.note && !isNotGenerated
            return (
              <div key={record.key} className="py-4 first:pt-0 last:pb-0">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0 space-y-1">
                    <div className="flex items-center gap-2">
                      <Badge variant="info">{record.type}</Badge>
                      <span className="font-mono text-sm text-on-surface break-all">{record.name}</span>
                    </div>
                    {record.value !== null ? (
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="font-mono text-xs text-on-surface-muted break-all">{record.value}</span>
                        <button
                          onClick={() => handleCopy(record.value!)}
                          className="p-1 text-on-surface-muted hover:text-primary rounded"
                          title="Copy value"
                          aria-label={`Copy ${record.name} value`}
                        >
                          <Copy className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ) : isNotGenerated ? (
                      <div className="space-y-1">
                        <Button size="sm" variant="secondary" onClick={() => setShowDkimConfirm(true)}>
                          Generate DKIM key
                        </Button>
                        {extraNote && (
                          <p className="text-xs text-on-surface-muted">{extraNote}</p>
                        )}
                      </div>
                    ) : null}
                    {noteVisible && (
                      <p className="text-xs text-on-surface-muted">{record.note}</p>
                    )}
                  </div>
                  <div className="shrink-0 pt-0.5">{renderStatus(record)}</div>
                </div>

                {result?.status === 'incorrect' && result.found_values.length > 0 && (
                  <div className="mt-2 space-y-0.5">
                    <p className="text-xs text-on-surface-muted">DNS currently returns:</p>
                    {result.found_values.map((found) => (
                      <p key={found} className="font-mono text-xs text-on-surface-muted break-all">{found}</p>
                    ))}
                  </div>
                )}

                {result?.status === 'error' && result.detail && (
                  <p className="mt-2 text-xs text-on-surface-muted">{result.detail}</p>
                )}
              </div>
            )
          })}
        </div>
      </Card>

      <ConfirmDialog
        open={showDkimConfirm}
        onClose={() => setShowDkimConfirm(false)}
        onConfirm={handleDkimRegenerate}
        title="Regenerate DKIM Key"
        message={`Generates a new DKIM key for ${domain.domain}.`}
        impact="DNS record must be updated; mail may fail DKIM checks until then."
        variant="warning"
        confirmLabel="Regenerate"
        loading={dkimMutation.isPending}
      />
    </div>
  )
}
