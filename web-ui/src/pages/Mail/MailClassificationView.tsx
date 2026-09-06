import { useState } from 'react'
import { Brain, RefreshCw, CheckCircle, AlertTriangle, Inbox, Shield, XCircle } from 'lucide-react'
import { useMailMessages, useReclassifyMessage, useMessageAction } from '../../hooks/useApi'
import { DataTable, EmptyState, ConfirmDialog, toast, Badge } from '../../components/ui'
import type { MailMessage } from '../../types'

interface MailClassificationViewProps {
  domainId: number
}

const CATEGORY_ICONS: Record<string, React.ReactNode> = {
  important: <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />,
  newsletter: <Inbox className="w-3.5 h-3.5 text-blue-600" />,
  promotional: <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />,
  social: <Brain className="w-3.5 h-3.5 text-violet-600" />,
  spam: <XCircle className="w-3.5 h-3.5 text-red-600" />,
  phishing: <Shield className="w-3.5 h-3.5 text-red-700" />,
  legitimate: <CheckCircle className="w-3.5 h-3.5 text-gray-600" />,
}

const CATEGORY_VARIANT: Record<string, 'success' | 'danger' | 'warning' | 'info' | 'neutral'> = {
  important: 'success',
  newsletter: 'info',
  promotional: 'warning',
  social: 'info',
  spam: 'danger',
  phishing: 'danger',
  legitimate: 'neutral',
}

export function MailClassificationView({ domainId }: MailClassificationViewProps) {
  const [filterCategory, setFilterCategory] = useState<string>('')
  const [actionTarget, setActionTarget] = useState<MailMessage | null>(null)
  const [actionType, setActionType] = useState<string>('')

  const { data: messages, isLoading } = useMailMessages(domainId, filterCategory ? { category: filterCategory } : undefined)
  const reclassifyMutation = useReclassifyMessage(actionTarget?.id || 0)
  const actionMutation = useMessageAction(actionTarget?.id || 0)

  const columns = [
    {
      key: 'subject',
      header: 'Subject',
      render: (msg: MailMessage) => (
        <span className="text-sm text-on-surface truncate max-w-[240px] block">{msg.subject || '(no subject)'}</span>
      ),
    },
    {
      key: 'sender',
      header: 'From',
      render: (msg: MailMessage) => (
        <span className="text-sm text-on-surface-muted">{msg.sender}</span>
      ),
    },
    {
      key: 'category',
      header: 'Category',
      render: (msg: MailMessage) => (
        <Badge variant={CATEGORY_VARIANT[msg.llm_category ?? ''] ?? 'neutral'} icon={Brain}>
          <span className="inline-flex items-center gap-1">
            {msg.llm_category && CATEGORY_ICONS[msg.llm_category]}
            {msg.llm_category || 'Pending'}
          </span>
        </Badge>
      ),
    },
    {
      key: 'confidence',
      header: 'Confidence',
      render: (msg: MailMessage) => (
        msg.llm_confidence ? (
          <span className="text-sm text-on-surface-muted">{Math.round(msg.llm_confidence * 100)}%</span>
        ) : (
          <span className="text-xs text-on-surface-muted">—</span>
        )
      ),
    },
    {
      key: 'action',
      header: 'Status',
      render: (msg: MailMessage) => (
        <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
          msg.action_taken === 'deliver' ? 'bg-success-subtle text-success' :
          msg.action_taken === 'quarantine' ? 'bg-warning-subtle text-warning' :
          msg.action_taken === 'reject' ? 'bg-danger-subtle text-danger' :
          'bg-neutral-subtle text-on-surface-muted'
        }`}>
          {msg.action_taken}
        </span>
      ),
    },
  ]

  const handleAction = async () => {
    if (!actionTarget || !actionType) return
    if (actionType === 'reclassify') {
      await reclassifyMutation.mutateAsync()
      toast.success('Message reclassified')
    } else {
      await actionMutation.mutateAsync({ action: actionType, reason: `Admin override: ${actionType}` })
      toast.success(`Message ${actionType === 'deliver' ? 'delivered' : 'quarantined'}`)
    }
    setActionTarget(null)
    setActionType('')
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <select
          value={filterCategory}
          onChange={(e) => setFilterCategory(e.target.value)}
          className="h-9 rounded-card border border-border bg-surface-card px-3 text-sm text-on-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
        >
          <option value="">All Categories</option>
          <option value="important">Important</option>
          <option value="newsletter">Newsletter</option>
          <option value="promotional">Promotional</option>
          <option value="social">Social</option>
          <option value="spam">Spam</option>
          <option value="phishing">Phishing</option>
          <option value="legitimate">Legitimate</option>
        </select>
        <p className="text-sm text-on-surface-muted">
          {messages?.length || 0} messages
        </p>
      </div>

      <DataTable
        columns={columns}
        data={messages || []}
        keyExtractor={(msg) => msg.id}
        searchable
        searchPlaceholder="Search messages…"
        isLoading={isLoading}
        rowActions={(msg) => (
          <div className="flex items-center gap-1">
            <button
              onClick={() => { setActionTarget(msg); setActionType('reclassify') }}
              className="p-1 text-on-surface-muted hover:text-primary rounded"
              title="Reclassify"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            <button
              onClick={() => { setActionTarget(msg); setActionType('deliver') }}
              className="p-1 text-on-surface-muted hover:text-success rounded"
              title="Deliver"
            >
              <CheckCircle className="w-4 h-4" />
            </button>
            <button
              onClick={() => { setActionTarget(msg); setActionType('quarantine') }}
              className="p-1 text-on-surface-muted hover:text-warning rounded"
              title="Quarantine"
            >
              <AlertTriangle className="w-4 h-4" />
            </button>
          </div>
        )}
        emptyContent={
          <EmptyState
            icon={Brain}
            title="No classified messages"
            description="Emails will appear here once they are processed by the LLM classifier."
          />
        }
      />

      <ConfirmDialog
        open={!!actionTarget && !!actionType}
        onClose={() => { setActionTarget(null); setActionType('') }}
        onConfirm={handleAction}
        title={actionType === 'reclassify' ? 'Reclassify Message' : `${actionType.charAt(0).toUpperCase() + actionType.slice(1)} Message`}
        message={actionType === 'reclassify'
          ? `Reclassify message from ${actionTarget?.sender}?`
          : `Are you sure you want to ${actionType} this message from ${actionTarget?.sender}?`
        }
        variant="warning"
        confirmLabel={actionType === 'reclassify' ? 'Reclassify' : actionType === 'deliver' ? 'Deliver' : 'Quarantine'}
        loading={reclassifyMutation.isPending || actionMutation.isPending}
      />
    </div>
  )
}
