import { useState } from 'react'
import { Field, Input, Switch, Button } from '../ui'
import type { RoutingRule, RoutingRuleCreate, RoutingRuleUpdate } from '../../types'

interface RoutingRuleFormProps {
  initial?: RoutingRule
  onSubmit: (data: RoutingRuleCreate | RoutingRuleUpdate) => void
  onCancel: () => void
  loading: boolean
}

export function RoutingRuleForm({ initial, onSubmit, onCancel, loading }: RoutingRuleFormProps) {
  const [name, setName] = useState(initial?.name || '')
  const [enabled, setEnabled] = useState(initial?.enabled ?? true)
  const [sourceNetwork, setSourceNetwork] = useState(initial?.source_network || '')
  const [destNetwork, setDestNetwork] = useState(initial?.dest_network || '')
  const [service, setService] = useState(initial?.service || '')
  const [inboundInterface, setInboundInterface] = useState(initial?.inbound_interface || '')
  const [gateway, setGateway] = useState(initial?.gateway || '')
  const [outboundInterface, setOutboundInterface] = useState(initial?.outbound_interface || '')
  const [mark, setMark] = useState(initial?.mark?.toString() || '')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const payload: RoutingRuleCreate = {
      name,
      enabled,
      source_network: sourceNetwork || undefined,
      dest_network: destNetwork || undefined,
      service: service || undefined,
      inbound_interface: inboundInterface || undefined,
      gateway: gateway || undefined,
      outbound_interface: outboundInterface || undefined,
      mark: mark ? parseInt(mark) : undefined,
      order_index: initial?.order_index,
    }
    onSubmit(payload)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Field label="Name" required>
        <Input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Route DMZ to WAN"
          required
        />
      </Field>

      <div className="flex items-center gap-2">
        <Switch
          checked={enabled}
          onCheckedChange={setEnabled}
          aria-label="Enabled"
        />
        <span className="text-sm text-on-surface">Enabled</span>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Field label="Source Network">
          <Input
            type="text"
            value={sourceNetwork}
            onChange={(e) => setSourceNetwork(e.target.value)}
            placeholder="10.0.0.0/24"
          />
        </Field>
        <Field label="Dest Network">
          <Input
            type="text"
            value={destNetwork}
            onChange={(e) => setDestNetwork(e.target.value)}
            placeholder="0.0.0.0/0"
          />
        </Field>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Field label="Service">
          <Input
            type="text"
            value={service}
            onChange={(e) => setService(e.target.value)}
            placeholder="tcp/80"
          />
        </Field>
        <Field label="Inbound Interface">
          <Input
            type="text"
            value={inboundInterface}
            onChange={(e) => setInboundInterface(e.target.value)}
            placeholder="eth0"
          />
        </Field>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Field label="Gateway">
          <Input
            type="text"
            value={gateway}
            onChange={(e) => setGateway(e.target.value)}
            placeholder="192.168.1.1"
          />
        </Field>
        <Field label="Outbound Interface">
          <Input
            type="text"
            value={outboundInterface}
            onChange={(e) => setOutboundInterface(e.target.value)}
            placeholder="eth1"
          />
        </Field>
      </div>

      <Field label="Firewall Mark (fwmark)">
        <Input
          type="number"
          value={mark}
          onChange={(e) => setMark(e.target.value)}
          placeholder="100"
        />
      </Field>

      <div className="flex items-center justify-end gap-2 pt-4">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" loading={loading}>
          {initial ? 'Update' : 'Create'}
        </Button>
      </div>
    </form>
  )
}
