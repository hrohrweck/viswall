import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Shield, Search, Sun, Moon, LogOut, Monitor, Menu, X } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import * as DropdownMenuPrimitive from '@radix-ui/react-dropdown-menu'
import { useAuthStore } from '../stores/auth'
import { useThemeStore, type Theme } from '../stores/theme'
import { useCommandPaletteStore } from '../stores/commandPalette'
import { useSidebarStore } from '../stores/sidebar'
import { Breadcrumbs, type BreadcrumbItem } from './ui/Breadcrumbs'
import { IconButton } from './ui/Button'
import { InstanceSwitcher } from './ui/InstanceSwitcher'
import {
  DropdownMenu,
  Content as DropdownMenuContent,
  Item as DropdownMenuItem,
  Separator as DropdownMenuSeparator,
} from './ui/DropdownMenu'

/** Human-readable labels for known route segments. */
const CRUMB_LABELS: Record<string, string> = {
  instances: 'Instances',
  firewall: 'Firewall',
  nat: 'NAT Rules',
  routing: 'Routing',
  traffic: 'Traffic Shaping',
  vpn: 'VPN',
  dns: 'DNS',
  dhcp: 'DHCP',
  mail: 'Mail',
  users: 'Users',
  metrics: 'Metrics',
  audit: 'Audit Logs',
  settings: 'Settings',
  admin: 'Admin',
  llm: 'LLM Providers',
  create: 'Create',
  simulator: 'Simulator',
  tests: 'Tests',
  domains: 'Domains',
  servers: 'Servers',
}

function labelFor(segment: string): string {
  return CRUMB_LABELS[segment] ?? segment.charAt(0).toUpperCase() + segment.slice(1)
}

function buildCrumbs(pathname: string): BreadcrumbItem[] {
  const segments = pathname.split('/').filter(Boolean)
  const crumbs: BreadcrumbItem[] = [{ label: 'Home', to: '/' }]

  let path = ''
  for (const seg of segments) {
    path += `/${seg}`
    crumbs.push({ label: labelFor(seg), to: path })
  }

  // Last item should not have `to` (renders as plain text in Breadcrumbs).
  if (crumbs.length > 1) {
    const last = crumbs[crumbs.length - 1]
    crumbs[crumbs.length - 1] = { label: last.label }
  }

  return crumbs
}

/** Cycle: light → dark → system */
function nextTheme(current: Theme): Theme {
  if (current === 'light') return 'dark'
  if (current === 'dark') return 'system'
  return 'light'
}

function themeIconComponent(theme: Theme): LucideIcon {
  if (theme === 'dark') return Moon
  if (theme === 'system') return Monitor
  return Sun
}

export function Header() {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const theme = useThemeStore((s) => s.theme)
  const setTheme = useThemeStore((s) => s.setTheme)
  const mobileOpen = useSidebarStore((s) => s.mobileOpen)
  const setMobileOpen = useSidebarStore((s) => s.setMobileOpen)

  const crumbs = buildCrumbs(location.pathname)
  const openPalette = useCommandPaletteStore((s) => s.setOpen)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const initials = user
    ? user.username.slice(0, 2).toUpperCase()
    : '??'

  return (
    <header className="h-14 border-b border-border bg-surface-card flex items-center px-4 gap-4 shrink-0">
      {/* LEFT — hamburger + logo + breadcrumbs */}
      <div className="flex items-center gap-3 min-w-0 flex-1">
        <IconButton
          icon={mobileOpen ? X : Menu}
          label={mobileOpen ? 'Close navigation' : 'Open navigation'}
          variant="ghost"
          size="md"
          onClick={() => setMobileOpen(!mobileOpen)}
          className="lg:hidden"
        />
        <Link to="/" className="flex items-center gap-1.5 shrink-0">
          <Shield className="w-5 h-5 text-primary" />
          <span className="text-sm font-bold text-on-surface hidden sm:inline">
            Viswall
          </span>
        </Link>
        <Breadcrumbs items={crumbs} />
      </div>

      {/* CENTER-LEFT — global instance switcher */}
      <InstanceSwitcher />

      {/* RIGHT — search, theme, user menu */}
      <div className="flex items-center gap-1">
        {/* Search → opens command palette */}
        <button
          type="button"
          data-testid="command-palette-trigger"
          onClick={() => openPalette(true)}
          className="inline-flex items-center gap-1.5 h-9 px-3 rounded-card text-sm text-on-surface-muted border border-border bg-surface-card hover:bg-surface-elevated transition-colors"
        >
          <Search className="w-4 h-4" />
          <span className="hidden md:inline">Search</span>
          <kbd className="hidden md:inline ml-1 rounded bg-surface-elevated px-1.5 py-0.5 text-xs font-mono text-on-surface-muted border border-border">
            ⌘K
          </kbd>
        </button>

        {/* Theme toggle */}
        <IconButton
          icon={themeIconComponent(theme)}
          label={`Theme: ${theme}`}
          variant="ghost"
          size="md"
          onClick={() => setTheme(nextTheme(theme))}
        />

        {/* User menu */}
        {user && (
          <DropdownMenu>
            <DropdownMenuPrimitive.Trigger asChild>
              <button
                type="button"
                aria-label="User menu"
                className="inline-flex items-center justify-center w-9 h-9 rounded-full bg-primary text-white text-xs font-bold hover:opacity-90 transition-opacity"
              >
                {initials}
              </button>
            </DropdownMenuPrimitive.Trigger>

            <DropdownMenuContent align="end" sideOffset={8}>
              <div className="px-3 py-2">
                <p className="text-sm font-medium text-on-surface">
                  {user.username}
                </p>
                <p className="text-xs text-on-surface-muted capitalize">
                  {user.role}
                </p>
              </div>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                disabled
                className="text-on-surface-muted cursor-default"
              >
                {user.username}
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                danger
                onClick={handleLogout}
                className="cursor-pointer"
              >
                <LogOut className="w-4 h-4 mr-2" />
                Logout
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>
    </header>
  )
}
