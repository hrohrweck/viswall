import { useState } from 'react'
import { Field, Input, Select, Switch, Button } from '../ui'
import type { QoSPolicy, QoSPolicyCreate, QoSPolicyUpdate } from '../../types'

interface TrafficPolicyFormProps {
  initial?: QoSPolicy
  onSubmit: (data: QoSPolicyCreate | QoSPolicyUpdate) => void
  onCancel: () => void
  loading: boolean
}

export function TrafficPolicyForm({ initial, onSubmit, onCancel, loading }: TrafficPolicyFormProps) {
  const [name, setName] = useState(initial?.name || '')
  const [description, setDescription] = useState(initial?.description || '')
  const [interfaceName, setInterfaceName] = useState(initial?.interface_name || 'eth0')
  const [algorithm, setAlgorithm] = useState<'cake' | 'fq_codel' | 'htb'>(
    (initial?.algorithm as 'cake' | 'fq_codel' | 'htb') || 'cake',
  )
  const [downloadKbps, setDownloadKbps] = useState(initial?.download_kbps || 100000)
  const [uploadKbps, setUploadKbps] = useState(initial?.upload_kbps || 50000)
  const [enabled, setEnabled] = useState(initial?.enabled ?? true)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (initial) {
      const payload: QoSPolicyUpdate = {
        name,
        description: description || undefined,
        enabled,
        algorithm,
        download_kbps: downloadKbps,
        upload_kbps: uploadKbps,
      }
      onSubmit(payload)
    } else {
      const payload: QoSPolicyCreate = {
        name,
        description: description || undefined,
        interface_name: interfaceName,
        algorithm,
        download_kbps: downloadKbps,
        upload_kbps: uploadKbps,
        enabled,
        classes: [],
      }
      onSubmit(payload)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Field label="Policy Name" required>
        <Input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
      </Field>

      <Field label="Description">
        <Input
          type="text"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </Field>

      <Field label="Interface" required>
        <Input
          type="text"
          value={interfaceName}
          onChange={(e) => setInterfaceName(e.target.value)}
          disabled={!!initial}
          required
        />
      </Field>

      <Field label="Algorithm">
        <Select
          value={algorithm}
          onChange={(e) => setAlgorithm(e.target.value as 'cake' | 'fq_codel' | 'htb')}
        >
          <option value="cake">CAKE (Recommended)</option>
          <option value="fq_codel">FQ-CoDel</option>
          <option value="htb">HTB (Advanced)</option>
        </Select>
      </Field>

      <div className="grid grid-cols-2 gap-4">
        <Field label="Download (Kbps)" required>
          <Input
            type="number"
            value={downloadKbps}
            onChange={(e) => setDownloadKbps(Number(e.target.value))}
            min={1}
            required
          />
        </Field>
        <Field label="Upload (Kbps)" required>
          <Input
            type="number"
            value={uploadKbps}
            onChange={(e) => setUploadKbps(Number(e.target.value))}
            min={1}
            required
          />
        </Field>
      </div>

      <div className="flex items-center gap-2">
        <Switch
          checked={enabled}
          onCheckedChange={setEnabled}
          aria-label="Enable policy immediately"
        />
        <span className="text-sm text-on-surface">Enable policy immediately</span>
      </div>

      <div className="flex justify-end gap-3 pt-4">
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
