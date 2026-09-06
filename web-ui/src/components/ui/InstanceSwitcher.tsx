import { Server, ChevronDown, Check } from 'lucide-react'
import * as DropdownMenuPrimitive from '@radix-ui/react-dropdown-menu'
import { useInstances } from '../../hooks/useApi'
import { useInstanceStore } from '../../stores/instance'
import { Button } from './Button'
import {
  DropdownMenu,
  Content as DropdownMenuContent,
  Item as DropdownMenuItem,
} from './DropdownMenu'
import { cn } from '../../lib/utils'

/**
 * Map instance status to a Tailwind bg token class for the status dot.
 */
function statusDotClass(status: string): string {
  switch (status) {
    case 'active':
    case 'running':
    case 'online':
      return 'bg-emerald-500'
    case 'maintenance':
    case 'restarting':
      return 'bg-amber-500'
    case 'error':
      return 'bg-rose-500'
    default:
      return 'bg-gray-400'
  }
}

export function InstanceSwitcher() {
  const { data: instances, isLoading } = useInstances()
  const selectedInstanceId = useInstanceStore((s) => s.selectedInstanceId)
  const setSelectedInstance = useInstanceStore((s) => s.setSelectedInstance)

  const selected = instances?.find((i) => i.id === selectedInstanceId)

  if (isLoading) {
    return (
      <Button variant="secondary" size="sm" disabled>
        <Server className="w-4 h-4 animate-pulse" />
        <span className="text-sm">Loading…</span>
      </Button>
    )
  }

  if (!instances || instances.length === 0) {
    return (
      <Button variant="secondary" size="sm" disabled>
        <Server className="w-4 h-4" />
        <span className="text-sm">No instances</span>
      </Button>
    )
  }

  return (
    <DropdownMenu>
      <DropdownMenuPrimitive.Trigger asChild>
        <Button
          variant="secondary"
          size="sm"
          className="gap-1.5 max-w-[220px]"
          type="button"
        >
          <Server className="w-4 h-4 shrink-0" />
          {selected ? (
            <span className="flex items-center gap-1.5 min-w-0">
              <span
                className={cn(
                  'w-2 h-2 rounded-full shrink-0',
                  statusDotClass(selected.status),
                )}
              />
              <span className="truncate text-sm font-medium">
                {selected.name}
              </span>
              <span className="truncate font-mono text-xs text-on-surface-muted hidden sm:inline">
                {selected.hostname}
              </span>
            </span>
          ) : (
            <span className="text-sm text-on-surface-muted">
              Select instance
            </span>
          )}
          <ChevronDown className="w-3.5 h-3.5 shrink-0 text-on-surface-muted" />
        </Button>
      </DropdownMenuPrimitive.Trigger>

      <DropdownMenuContent
        align="start"
        className="w-[280px]"
        sideOffset={4}
      >
        {instances.map((inst) => (
          <DropdownMenuItem
            key={inst.id}
            onClick={() => setSelectedInstance(inst.id)}
            className="flex items-center gap-2 cursor-pointer"
          >
            <span
              className={cn(
                'w-2 h-2 rounded-full shrink-0',
                statusDotClass(inst.status),
              )}
            />
            <span className="flex-1 min-w-0">
              <span className="block text-sm font-medium truncate">
                {inst.name}
              </span>
              <span className="block font-mono text-xs text-on-surface-muted truncate">
                {inst.hostname}
              </span>
            </span>
            {selectedInstanceId === inst.id && (
              <Check className="w-4 h-4 shrink-0 text-primary" />
            )}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
