import { useInstances } from '../../hooks/useApi'
import { useInstanceStore } from '../../stores/instance'
import { ChevronDown, Server } from 'lucide-react'
import { useState, useRef, useEffect } from 'react'

export function InstanceSelector() {
  const { data: instances, isLoading } = useInstances()
  const { selectedInstanceId, setSelectedInstance } = useInstanceStore()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  const selected = instances?.find((i) => i.id === selectedInstanceId)

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-400 text-sm">
        Loading...
      </div>
    )
  }

  if (!instances || instances.length === 0) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-400 text-sm">
        No instances
      </div>
    )
  }

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm min-w-[200px]"
      >
        <Server className="w-4 h-4 text-gray-500" />
        <span className="flex-1 text-left truncate">
          {selected ? selected.name : 'Select instance...'}
        </span>
        <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <div className="absolute top-full left-0 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg z-50">
          {instances.map((instance) => (
            <button
              key={instance.id}
              onClick={() => {
                setSelectedInstance(instance.id)
                setOpen(false)
              }}
              className={`w-full text-left px-3 py-2 text-sm hover:bg-gray-50 flex items-center gap-2 ${
                instance.id === selectedInstanceId ? 'bg-primary-50 text-primary-700' : ''
              }`}
            >
              <Server className="w-4 h-4" />
              <span className="flex-1">{instance.name}</span>
              <span className="text-xs text-gray-400">{instance.hostname}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
