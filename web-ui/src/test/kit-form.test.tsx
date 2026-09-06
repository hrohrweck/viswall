import { useState } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Field, Label } from '../components/ui/Field'
import { Input, Textarea } from '../components/ui/Input'
import { Select } from '../components/ui/Select'
import { Switch, Checkbox, Radio } from '../components/ui/Switch'

/* -------------------------------------------------------------------------- */
/*  Kit form tests — accessible form controls + Field ARIA wiring              */
/* -------------------------------------------------------------------------- */

describe('Field', () => {
  it('links label to input via htmlFor/id — clicking label focuses input', async () => {
    const user = userEvent.setup()
    render(
      <Field label="Username">
        <Input placeholder="Enter username" />
      </Field>,
    )
    const label = screen.getByText('Username')
    const input = screen.getByPlaceholderText('Enter username')
    // label htmlFor should match the input's id
    expect(label).toHaveAttribute('for', input.id)
    await user.click(label)
    expect(input).toHaveFocus()
  })

  it('wires helper text id into aria-describedby', () => {
    render(
      <Field label="Email" helper="We won't share this">
        <Input placeholder="you@example.com" />
      </Field>,
    )
    const input = screen.getByPlaceholderText('you@example.com')
    const helper = screen.getByText("We won't share this")
    expect(helper).toHaveAttribute('id')
    expect(input.getAttribute('aria-describedby')).toContain(helper.id)
  })

  it('error prop → role="alert" text + aria-invalid on input + border-danger class', () => {
    render(
      <Field label="Email" error="Email is required">
        <Input placeholder="you@example.com" />
      </Field>,
    )
    const alert = screen.getByRole('alert')
    expect(alert).toHaveTextContent('Email is required')
    const input = screen.getByPlaceholderText('you@example.com')
    expect(input).toHaveAttribute('aria-invalid', 'true')
    expect(input.getAttribute('aria-describedby')).toContain(alert.id)
    expect(input.className).toContain('border-danger')
  })

  it('error takes precedence over helper', () => {
    render(
      <Field label="Name" helper="Optional hint" error="Required">
        <Input placeholder="name" />
      </Field>,
    )
    expect(screen.getByRole('alert')).toHaveTextContent('Required')
    expect(screen.queryByText('Optional hint')).not.toBeInTheDocument()
  })

  it('renders required indicator', () => {
    render(
      <Field label="Name" required>
        <Input placeholder="name" />
      </Field>,
    )
    expect(screen.getByText('*')).toHaveAttribute('aria-hidden', 'true')
  })
})

describe('Input', () => {
  it('mono prop adds font-mono class', () => {
    render(<Input mono data-testid="mono-input" />)
    expect(screen.getByTestId('mono-input').className).toContain('font-mono')
  })

  it('does not add font-mono when mono is false', () => {
    render(<Input data-testid="plain-input" />)
    expect(screen.getByTestId('plain-input').className).not.toContain('font-mono')
  })

  it('applies aria-invalid styling', () => {
    render(<Input aria-invalid="true" data-testid="invalid-input" />)
    expect(screen.getByTestId('invalid-input').className).toContain('border-danger')
  })

  it('forwards ref', () => {
    const ref = vi.fn()
    render(<Input ref={ref} />)
    expect(ref).toHaveBeenCalledWith(expect.any(HTMLInputElement))
  })
})

describe('Textarea', () => {
  it('renders with rows prop', () => {
    render(<Textarea rows={5} data-testid="textarea" />)
    expect(screen.getByTestId('textarea')).toHaveAttribute('rows', '5')
  })

  it('applies aria-invalid styling', () => {
    render(<Textarea aria-invalid="true" data-testid="textarea" />)
    expect(screen.getByTestId('textarea').className).toContain('border-danger')
  })

  it('forwards ref', () => {
    const ref = vi.fn()
    render(<Textarea ref={ref} />)
    expect(ref).toHaveBeenCalledWith(expect.any(HTMLTextAreaElement))
  })
})

describe('Select', () => {
  it('renders options and fires onChange', async () => {
    const onChange = vi.fn()
    const user = userEvent.setup()
    render(
      <Select onChange={onChange} data-testid="select">
        <option value="a">Alpha</option>
        <option value="b">Bravo</option>
      </Select>,
    )
    const select = screen.getByTestId('select')
    await user.selectOptions(select, 'b')
    expect(onChange).toHaveBeenCalled()
    expect(select).toHaveValue('b')
  })

  it('forwards ref', () => {
    const ref = vi.fn()
    render(
      <Select ref={ref}>
        <option value="x">X</option>
      </Select>,
    )
    expect(ref).toHaveBeenCalledWith(expect.any(HTMLSelectElement))
  })

  it('applies aria-invalid styling', () => {
    render(
      <Select aria-invalid="true" data-testid="select">
        <option value="x">X</option>
      </Select>,
    )
    expect(screen.getByTestId('select').className).toContain('border-danger')
  })
})

describe('Switch', () => {
  it('toggles via click and fires onCheckedChange', async () => {
    const onCheckedChange = vi.fn()
    const user = userEvent.setup()
    function ControlledSwitch() {
      const [checked, setChecked] = useState(false)
      return (
        <Switch
          aria-label="Toggle feature"
          checked={checked}
          onCheckedChange={(val) => {
            setChecked(val)
            onCheckedChange(val)
          }}
        />
      )
    }
    render(<ControlledSwitch />)
    const toggle = screen.getByRole('switch', { name: 'Toggle feature' })
    expect(toggle).toHaveAttribute('data-state', 'unchecked')
    await user.click(toggle)
    expect(onCheckedChange).toHaveBeenCalledWith(true)
    expect(toggle).toHaveAttribute('data-state', 'checked')
  })

  it('is disabled when disabled prop is set', () => {
    render(<Switch disabled aria-label="Disabled switch" />)
    expect(screen.getByRole('switch')).toBeDisabled()
  })
})

describe('Checkbox', () => {
  it('renders as checkbox and can be toggled', async () => {
    const user = userEvent.setup()
    render(<Checkbox data-testid="cb" />)
    const cb = screen.getByTestId('cb') as HTMLInputElement
    expect(cb.type).toBe('checkbox')
    expect(cb.checked).toBe(false)
    await user.click(cb)
    expect(cb.checked).toBe(true)
  })

  it('forwards ref', () => {
    const ref = vi.fn()
    render(<Checkbox ref={ref} />)
    expect(ref).toHaveBeenCalledWith(expect.any(HTMLInputElement))
  })
})

describe('Radio', () => {
  it('renders as radio and can be selected', async () => {
    const user = userEvent.setup()
    render(
      <div>
        <Radio name="group" value="a" data-testid="radio-a" />
        <Radio name="group" value="b" data-testid="radio-b" />
      </div>,
    )
    const radioA = screen.getByTestId('radio-a') as HTMLInputElement
    const radioB = screen.getByTestId('radio-b') as HTMLInputElement
    expect(radioA.type).toBe('radio')
    await user.click(radioA)
    expect(radioA.checked).toBe(true)
    await user.click(radioB)
    expect(radioA.checked).toBe(false)
    expect(radioB.checked).toBe(true)
  })

  it('forwards ref', () => {
    const ref = vi.fn()
    render(<Radio ref={ref} name="test" />)
    expect(ref).toHaveBeenCalledWith(expect.any(HTMLInputElement))
  })
})

describe('Label', () => {
  it('renders with htmlFor', () => {
    render(<Label htmlFor="my-input">Name</Label>)
    expect(screen.getByText('Name')).toHaveAttribute('for', 'my-input')
  })

  it('applies custom className', () => {
    render(<Label className="custom" data-testid="label">Name</Label>)
    expect(screen.getByTestId('label').className).toContain('custom')
    expect(screen.getByTestId('label').className).toContain('font-medium')
  })
})
