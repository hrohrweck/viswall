import { useState } from 'react'
import { Button, Field, Input } from '../ui'
import { DHCPSubnetType } from '../../types'
import type { DHCPOptionCreate } from '../../types'

interface DHCPOptionFormProps {
  subnetType: DHCPSubnetType
  loading: boolean
  onSubmit: (payload: DHCPOptionCreate) => void
}

export function DHCPOptionForm({ subnetType, loading, onSubmit }: DHCPOptionFormProps) {
  const [optionCode, setOptionCode] = useState(subnetType === DHCPSubnetType.V4 ? 66 : 23)
  const [optionName, setOptionName] = useState(
    subnetType === DHCPSubnetType.V4 ? 'tftp-server-name' : 'dns-servers',
  )
  const [optionValue, setOptionValue] = useState(
    subnetType === DHCPSubnetType.V4 ? '192.168.10.2' : '2001:db8::53',
  )

  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault()
        onSubmit({
          option_code: optionCode,
          option_name: optionName,
          option_value: optionValue,
          type: subnetType,
        })
      }}
    >
      <Field label="Option Code">
        <Input
          type="number"
          value={optionCode}
          onChange={(event) => setOptionCode(Number(event.target.value))}
        />
      </Field>
      <Field label="Option Name">
        <Input value={optionName} onChange={(event) => setOptionName(event.target.value)} />
      </Field>
      <Field label="Option Value">
        <Input mono value={optionValue} onChange={(event) => setOptionValue(event.target.value)} />
      </Field>
      <div className="flex justify-end">
        <Button type="submit" loading={loading}>
          Create Option
        </Button>
      </div>
    </form>
  )
}
