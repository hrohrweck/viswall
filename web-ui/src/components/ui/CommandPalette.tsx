import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Command } from 'cmdk'
import { useAuthStore } from '../../stores/auth'
import { useInstanceStore } from '../../stores/instance'
import { useCommandPaletteStore } from '../../stores/commandPalette'
import { useInstances } from '../../hooks/useApi'

/** Sidebar routes for the PAGES group. */
const PAGES = [
  { path: '/', label: 'Dashboard' },
  { path: '/instances', label: 'Instances' },
  { path: '/metrics', label: 'Metrics' },
  { path: '/firewall', label: 'Firewall' },
  { path: '/firewall/simulator', label: 'Simulator' },
  { path: '/firewall/tests', label: 'Test Suite' },
  { path: '/firewall/nat', label: 'NAT Rules' },
  { path: '/routing', label: 'Routing' },
  { path: '/traffic', label: 'Traffic Shaping' },
  { path: '/vpn', label: 'VPN' },
  { path: '/dns', label: 'DNS' },
  { path: '/dhcp', label: 'DHCP' },
  { path: '/mail', label: 'Mail' },
  { path: '/users', label: 'Users' },
  { path: '/audit', label: 'Audit Logs' },
  { path: '/admin/llm', label: 'LLM Providers' },
  { path: '/settings', label: 'Settings' },
]

/** Admin-only paths — same set as in Sidebar.tsx. */
const ADMIN_PATHS = new Set(['/audit', '/admin/llm'])

/** Navigation-only actions for the ACTIONS group. */
const ACTIONS = [
  { path: '/instances', label: 'Add instance' },
  { path: '/vpn/create', label: 'New VPN server' },
  { path: '/mail/domains/create', label: 'Add mail domain' },
  { path: '/metrics', label: 'View metrics' },
]

export function CommandPalette() {
  const navigate = useNavigate()
  const { open, setOpen } = useCommandPaletteStore()
  const { user } = useAuthStore()
  const setSelectedInstance = useInstanceStore((s) => s.setSelectedInstance)
  const { data: instances } = useInstances()

  const isAdmin = user?.role === 'admin' || user?.role === 'superadmin'

  /* ── Global ⌘K / Ctrl+K toggle (reads store directly to avoid stale closure). ── */
  useEffect(() => {
    function handleKeydown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        const store = useCommandPaletteStore.getState()
        store.setOpen(!store.open)
      }
    }
    document.addEventListener('keydown', handleKeydown)
    return () => document.removeEventListener('keydown', handleKeydown)
  }, [])

  function handlePageSelect(path: string) {
    setOpen(false)
    navigate(path)
  }

  function handleInstanceSelect(id: number) {
    setSelectedInstance(id)
    setOpen(false)
    navigate(`/instances/${id}`)
  }

  const visiblePages = PAGES.filter((p) => !ADMIN_PATHS.has(p.path) || isAdmin)

  /* Shared Tailwind class strings — avoids repetition across three groups. */
  const groupHeadingClass =
    '[&>[cmdk-group-heading]]:px-2 [&>[cmdk-group-heading]]:py-1.5 [&>[cmdk-group-heading]]:text-xs [&>[cmdk-group-heading]]:uppercase [&>[cmdk-group-heading]]:tracking-wide [&>[cmdk-group-heading]]:text-on-surface-muted [&>[cmdk-group-heading]]:font-medium'

  const itemClass =
    'flex items-center px-2 py-2 rounded-md text-sm cursor-pointer data-[selected]:bg-primary-subtle data-[selected]:text-primary'

  return (
    <Command.Dialog
      open={open}
      onOpenChange={setOpen}
      label="Command palette"
      overlayClassName="fixed inset-0 z-50 bg-black/50"
      contentClassName="fixed top-[20%] left-1/2 -translate-x-1/2 z-50 w-full max-w-lg bg-surface-card border border-border rounded-card shadow-lg text-on-surface overflow-hidden"
    >
      <Command.Input
        placeholder="Search pages, instances, actions…"
        className="w-full px-4 py-3 bg-transparent text-on-surface placeholder:text-on-surface-muted outline-none border-b border-border"
      />
      <Command.List className="max-h-80 overflow-y-auto p-2">
        <Command.Empty className="py-6 text-center text-sm text-on-surface-muted">
          No results.
        </Command.Empty>

        {/* ── PAGES ── */}
        <Command.Group heading="Pages" className={groupHeadingClass}>
          {visiblePages.map((p) => (
            <Command.Item
              key={p.path}
              value={p.label}
              onSelect={() => handlePageSelect(p.path)}
              className={itemClass}
            >
              {p.label}
            </Command.Item>
          ))}
        </Command.Group>

        {/* ── INSTANCES ── */}
        {instances && instances.length > 0 && (
          <Command.Group heading="Instances" className={groupHeadingClass}>
            {instances.map((inst) => (
              <Command.Item
                key={inst.id}
                value={inst.name}
                keywords={[inst.name, inst.hostname]}
                onSelect={() => handleInstanceSelect(inst.id)}
                className={itemClass}
              >
                {inst.name}
              </Command.Item>
            ))}
          </Command.Group>
        )}

        {/* ── ACTIONS ── */}
        <Command.Group heading="Actions" className={groupHeadingClass}>
          {ACTIONS.map((a) => (
            <Command.Item
              key={a.label}
              value={a.label}
              onSelect={() => handlePageSelect(a.path)}
              className={itemClass}
            >
              {a.label}
            </Command.Item>
          ))}
        </Command.Group>
      </Command.List>
    </Command.Dialog>
  )
}
