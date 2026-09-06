import { useState } from 'react'
import { Plus, Globe, ArrowRightLeft, Info } from 'lucide-react'
import { useInstanceStore } from '../stores/instance'
import { useNATRules, useCreateNATRule } from '../hooks/useApi'
import {
  Badge,
  Button,
  Card,
  Checkbox,
  DataTable,
  EmptyState,
  Field,
  Input,
  Modal,
  PageHeader,
  Select,
} from '../components/ui'
import { toast } from '../components/ui/Toaster'
import { getErrMsg } from '../lib/utils'
import type { NATRule, NATRuleCreate } from '../types'
import { NATType } from '../types'

/* ------------------------------------------------------------------ */
/*  NatRules                                                            */
/* ------------------------------------------------------------------ */

export function NatRules() {
  const { selectedInstanceId } = useInstanceStore()
  const { data: rules, isLoading, isError, refetch } = useNATRules(selectedInstanceId || 0)
  const createMutation = useCreateNATRule(selectedInstanceId || 0)

  const [showCreate, setShowCreate] = useState(false)

  const handleCreate = async (data: NATRuleCreate) => {
    createMutation.mutate(data, {
      onSuccess: () => {
        toast.success('NAT rule created')
        setShowCreate(false)
      },
      onError: (e) => toast.error(getErrMsg(e)),
    })
  }

  /* ── No instance selected ── */
  if (!selectedInstanceId) {
    return (
      <div>
        <PageHeader title="NAT Rules" />
        <Card className="mt-6">
          <div className="flex items-center gap-3 text-on-surface-muted">
            <Info className="h-5 w-5 shrink-0" />
            <p className="text-sm">Select an instance from the top bar to manage its NAT rules.</p>
          </div>
        </Card>
      </div>
    )
  }

  /* ── Columns ── */
  const columns = [
    {
      key: 'name',
      header: 'Rule',
      render: (rule: NATRule) => (
        <div>
          <p className="font-medium text-on-surface">{rule.name}</p>
          {rule.description && <p className="text-xs text-on-surface-muted">{rule.description}</p>}
        </div>
      ),
    },
    {
      key: 'type',
      header: 'Type',
      render: (rule: NATRule) => (
        <Badge variant="info">{rule.type.toUpperCase()}</Badge>
      ),
    },
    {
      key: 'interface',
      header: 'Interface',
      render: (rule: NATRule) => (
        <span className="text-sm text-on-surface-muted">{rule.interface || 'Any'}</span>
      ),
    },
    {
      key: 'source',
      header: 'Source',
      className: 'font-mono',
      render: (rule: NATRule) => (
        <span className="text-sm text-on-surface-muted">{rule.source_network || 'Any'}</span>
      ),
    },
    {
      key: 'dest',
      header: 'Destination',
      className: 'font-mono',
      render: (rule: NATRule) => (
        <span className="text-sm text-on-surface-muted">{rule.dest_network || 'Any'}</span>
      ),
    },
    {
      key: 'translation',
      header: 'Translation',
      render: (rule: NATRule) => (
        <span className="text-sm text-on-surface-muted">
          {rule.to_source || rule.to_destination || '-'}
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (rule: NATRule) => (
        <Badge variant={rule.enabled ? 'success' : 'neutral'}>
          {rule.enabled ? 'Enabled' : 'Disabled'}
        </Badge>
      ),
    },
  ]

  return (
    <div>
      <PageHeader
        title="NAT Rules"
        description="Manage source and destination NAT rules"
        primaryAction={
          <Button icon={Plus} onClick={() => setShowCreate(true)}>
            Add NAT Rule
          </Button>
        }
      />

      <div className="mt-6">
        <DataTable
          columns={columns}
          data={rules || []}
          keyExtractor={(rule) => rule.id}
          searchable
          searchPlaceholder="Search NAT rules…"
          isLoading={isLoading}
          isError={isError}
          onRetry={() => refetch()}
          emptyContent={
            <EmptyState
              icon={ArrowRightLeft}
              title="No NAT Rules"
              description="Create NAT rules to translate source or destination addresses for traffic flowing through this instance."
            />
          }
        />
      </div>

      {/* Create modal */}
      {showCreate && (
        <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Create NAT Rule">
          <NATRuleForm
            onSubmit={handleCreate}
            onCancel={() => setShowCreate(false)}
            isSubmitting={createMutation.isPending}
          />
        </Modal>
      )}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  NATRuleForm — visual refresh with kit components                   */
/* ------------------------------------------------------------------ */

interface NATRuleFormProps {
  onSubmit: (data: NATRuleCreate) => void
  onCancel: () => void
  isSubmitting: boolean
}

function NATRuleForm({ onSubmit, onCancel, isSubmitting }: NATRuleFormProps) {
  const [formData, setFormData] = useState<NATRuleCreate>({
    name: '',
    type: NATType.SNAT,
    enabled: true,
    interface: '',
    source_network: '',
    dest_network: '',
    to_source: '',
    to_destination: '',
    service_protocol: 'any',
    service_ports: '',
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Field label="Name" required>
        <Input
          type="text"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          placeholder="Rule name"
          required
        />
      </Field>

      <Field label="Type">
        <Select
          value={formData.type}
          onChange={(e) => setFormData({ ...formData, type: e.target.value as NATType })}
        >
          <option value={NATType.SNAT}>Source NAT (SNAT)</option>
          <option value={NATType.DNAT}>Destination NAT (DNAT)</option>
          <option value={NATType.MASQUERADE}>Masquerade</option>
        </Select>
      </Field>

      <Field label="Interface">
        <Input
          type="text"
          value={formData.interface}
          onChange={(e) => setFormData({ ...formData, interface: e.target.value })}
          placeholder="e.g. eth0"
        />
      </Field>

      <div className="grid grid-cols-2 gap-4">
        <Field label="Source Network">
          <Input
            type="text"
            value={formData.source_network}
            onChange={(e) => setFormData({ ...formData, source_network: e.target.value })}
            placeholder="e.g. 192.168.1.0/24"
          />
        </Field>
        <Field label="Destination Network">
          <Input
            type="text"
            value={formData.dest_network}
            onChange={(e) => setFormData({ ...formData, dest_network: e.target.value })}
            placeholder="e.g. 10.0.0.0/8"
          />
        </Field>
      </div>

      {formData.type !== 'masquerade' && (
        <div className="grid grid-cols-2 gap-4">
          <Field label={formData.type === 'snat' ? 'To Source' : 'To Destination'}>
            <Input
              type="text"
              value={formData.type === 'snat' ? formData.to_source : formData.to_destination}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  ...(formData.type === 'snat'
                    ? { to_source: e.target.value }
                    : { to_destination: e.target.value }),
                })
              }
              placeholder="e.g. 203.0.113.1"
            />
          </Field>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <Field label="Protocol">
          <Select
            value={formData.service_protocol}
            onChange={(e) => setFormData({ ...formData, service_protocol: e.target.value })}
          >
            <option value="any">Any</option>
            <option value="tcp">TCP</option>
            <option value="udp">UDP</option>
            <option value="icmp">ICMP</option>
          </Select>
        </Field>
        <Field label="Ports">
          <Input
            type="text"
            value={formData.service_ports}
            onChange={(e) => setFormData({ ...formData, service_ports: e.target.value })}
            placeholder="e.g. 80,443"
          />
        </Field>
      </div>

      <label htmlFor="nat-rule-enabled" className="flex items-center gap-2 cursor-pointer">
        <Checkbox
          id="nat-rule-enabled"
          checked={formData.enabled}
          onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
        />
        <span className="text-sm text-on-surface">Enable rule</span>
      </label>

      <div className="flex justify-end gap-3 pt-4">
        <Button type="button" variant="ghost" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" loading={isSubmitting}>
          Create
        </Button>
      </div>
    </form>
  )
}
