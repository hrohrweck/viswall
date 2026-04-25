import { useState } from 'react'
import { Brain, RefreshCw, CheckCircle, XCircle, AlertTriangle, Inbox, Shield } from 'lucide-react'
import { useMailMessages, useReclassifyMessage, useMessageAction } from '../../hooks/useApi'
import { DataTable, LoadingSpinner, EmptyState, ConfirmDialog } from '../../components/ui'
import type { MailMessage } from '../../types'

interface MailClassificationViewProps {
  domainId: number
}

const CATEGORY_ICONS: Record<string, React.ReactNode> = {
  important: <CheckCircle className="w-4 h-4 text-emerald-600" />,
  newsletter: <Inbox className="w-4 h-4 text-blue-600" />,
  promotional: <AlertTriangle className="w-4 h-4 text-amber-600" />,
  social: <Brain className="w-4 h-4 text-violet-600" />,
  spam: <XCircle className="w-4 h-4 text-red-600" />,
  phishing: <Shield className="w-4 h-4 text-red-700" />,
  legitimate: <CheckCircle className="w-4 h-4 text-gray-600" />,
}

const CATEGORY_COLORS: Record<string, string> = {
  important: 'bg-emerald-100 text-emerald-800',
  newsletter: 'bg-blue-100 text-blue-800',
  promotional: 'bg-amber-100 text-amber-800',
  social: 'bg-violet-100 text-violet-800',
  spam: 'bg-red-100 text-red-800',
  phishing: 'bg-red-200 text-red-900',
  legitimate: 'bg-gray-100 text-gray-800',
}

export function MailClassificationView({ domainId }: MailClassificationViewProps) {
  const [filterCategory, setFilterCategory] = useState<string>('')
  const [actionTarget, setActionTarget] = useState<MailMessage | null>(null)
  const [actionType, setActionType] = useState<string>('')

  const { data: messages, isLoading } = useMailMessages(domainId, filterCategory ? { category: filterCategory } : undefined)
  const reclassifyMutation = useReclassifyMessage(actionTarget?.id || 0)
  const actionMutation = useMessageAction(actionTarget?.id || 0)

  if (isLoading) return <LoadingSpinner />

  const columns = [
    {
      key: 'sender',
      header: 'From',
      render: (msg: MailMessage) => (
        <div>
          <p className="font-medium text-gray-900 text-sm">{msg.sender}</p>
          <p className="text-xs text-gray-500 truncate max-w-[200px]">{msg.subject || '(no subject)'}</p>
        </div>
      ),
    },
    {
      key: 'category',
      header: 'Category',
      render: (msg: MailMessage) => (
        <div className="flex items-center gap-2">
          {msg.llm_category && CATEGORY_ICONS[msg.llm_category]}
          <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${msg.llm_category ? CATEGORY_COLORS[msg.llm_category] || 'bg-gray-100 text-gray-800' : 'bg-gray-100 text-gray-500'}`}>
            {msg.llm_category || 'Pending'}
          </span>
        </div>
      ),
    },
    {
      key: 'confidence',
      header: 'Confidence',
      render: (msg: MailMessage) => (
        msg.llm_confidence ? (
          <div className="w-full max-w-[100px]">
            <div className="w-full bg-gray-200 rounded-full h-1.5">
              <div
                className={`h-1.5 rounded-full ${msg.llm_confidence > 0.8 ? 'bg-green-600' : msg.llm_confidence > 0.5 ? 'bg-yellow-500' : 'bg-red-500'}`}
                style={{ width: `${msg.llm_confidence * 100}%` }}
              />
            </div>
            <span className="text-xs text-gray-500">{Math.round(msg.llm_confidence * 100)}%</span>
          </div>
        ) : (
          <span className="text-xs text-gray-400">-</span>
        )
      ),
    },
    {
      key: 'action',
      header: 'Action',
      render: (msg: MailMessage) => (
        <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
          msg.action_taken === 'deliver' ? 'bg-green-100 text-green-800' :
          msg.action_taken === 'quarantine' ? 'bg-yellow-100 text-yellow-800' :
          msg.action_taken === 'reject' ? 'bg-red-100 text-red-800' :
          'bg-gray-100 text-gray-800'
        }`}>
          {msg.action_taken}
        </span>
      ),
    },
    {
      key: 'received',
      header: 'Received',
      render: (msg: MailMessage) => (
        <span className="text-xs text-gray-500">
          {new Date(msg.received_at).toLocaleString()}
        </span>
      ),
    },
    {
      key: 'actions',
      header: '',
      render: (msg: MailMessage) => (
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setActionTarget(msg)
              reclassifyMutation.mutate()
            }}
            disabled={reclassifyMutation.isPending}
            className="p-1 text-gray-400 hover:text-primary-600 rounded"
            title="Reclassify"
          >
            <RefreshCw className={`w-4 h-4 ${reclassifyMutation.isPending ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => { setActionTarget(msg); setActionType('deliver') }}
            className="p-1 text-gray-400 hover:text-green-600 rounded"
            title="Deliver"
          >
            <CheckCircle className="w-4 h-4" />
          </button>
          <button
            onClick={() => { setActionTarget(msg); setActionType('quarantine') }}
            className="p-1 text-gray-400 hover:text-yellow-600 rounded"
            title="Quarantine"
          >
            <AlertTriangle className="w-4 h-4" />
          </button>
        </div>
      ),
    },
  ]

  const handleAction = async () => {
    if (!actionTarget || !actionType) return
    await actionMutation.mutateAsync({ action: actionType, reason: `Admin override: ${actionType}` })
    setActionTarget(null)
    setActionType('')
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
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
        </div>
        <p className="text-sm text-gray-500">
          {messages?.length || 0} messages
        </p>
      </div>

      <DataTable
        columns={columns}
        data={messages || []}
        keyExtractor={(msg) => msg.id}
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
        title={`${actionType.charAt(0).toUpperCase() + actionType.slice(1)} Message`}
        message={`Are you sure you want to ${actionType} this message from ${actionTarget?.sender}?`}
        loading={actionMutation.isPending}
      />
    </div>
  )
}
