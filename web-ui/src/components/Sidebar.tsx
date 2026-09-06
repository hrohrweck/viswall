import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Server,
  Shield,
  Network,
  Database,
  Radio,
  Mail,
  Users,
  BarChart3,
  Settings,
  Gauge,
  Route,
  ClipboardList,
  Bot,
  Globe,
  ChevronsLeft,
  ChevronsRight,
  FlaskConical,
} from 'lucide-react'
import { useAuthStore } from '../stores/auth'
import { useSidebarStore } from '../stores/sidebar'
import { Tooltip } from './ui'

interface NavItem {
  path: string
  label: string
  icon: React.ComponentType<{ className?: string }>
  badge?: string
}

interface NavGroup {
  label: string
  items: NavItem[]
  adminOnly?: boolean
}

const navGroups: NavGroup[] = [
  {
    label: 'Overview',
    items: [
      { path: '/', label: 'Dashboard', icon: LayoutDashboard },
      { path: '/instances', label: 'Instances', icon: Server },
      { path: '/metrics', label: 'Metrics', icon: BarChart3 },
    ],
  },
  {
    label: 'Network',
    items: [
      { path: '/firewall', label: 'Firewall', icon: Shield },
      { path: '/firewall/simulator', label: 'Simulator', icon: FlaskConical, badge: 'Preview' },
      { path: '/firewall/tests', label: 'Test Suite', icon: FlaskConical, badge: 'Preview' },
      { path: '/firewall/nat', label: 'NAT Rules', icon: Globe },
      { path: '/routing', label: 'Routing', icon: Route },
      { path: '/traffic', label: 'Traffic Shaping', icon: Gauge },
      { path: '/vpn', label: 'VPN', icon: Network },
    ],
  },
  {
    label: 'Services',
    items: [
      { path: '/dns', label: 'DNS', icon: Database },
      { path: '/dhcp', label: 'DHCP', icon: Radio },
      { path: '/mail', label: 'Mail', icon: Mail },
    ],
  },
  {
    label: 'Administration',
    items: [
      { path: '/users', label: 'Users', icon: Users },
      { path: '/audit', label: 'Audit Logs', icon: ClipboardList },
      { path: '/admin/llm', label: 'LLM Providers', icon: Bot },
      { path: '/settings', label: 'Settings', icon: Settings },
    ],
  },
]

const adminPaths = new Set(['/audit', '/admin/llm'])
const subItemPaths = new Set(['/firewall/simulator', '/firewall/tests'])

export function Sidebar() {
  const { user } = useAuthStore()
  const { collapsed, setCollapsed } = useSidebarStore()
  const isAdmin = user?.role === 'admin' || user?.role === 'superadmin'

  return (
    <aside
      className={`h-full flex flex-col border-r border-border bg-surface-card transition-[width] duration-200 ${
        collapsed ? 'w-16' : 'w-64'
      }`}
    >
      <nav className="flex-1 overflow-y-auto p-2">
        {navGroups.map((group) => {
          const visibleItems = group.items.filter(
            (item) => !adminPaths.has(item.path) || isAdmin
          )
          if (visibleItems.length === 0) return null

          return (
            <div key={group.label} className="mb-2">
              {!collapsed && (
                <div className="px-3 py-1.5 text-[11px] uppercase tracking-wide text-on-surface-muted font-medium">
                  {group.label}
                </div>
              )}
              <ul>
                {visibleItems.map(({ path, label, icon: Icon, badge }) => {
                  const isSubItem = subItemPaths.has(path)
                  const navLink = (
                    <NavLink
                      to={path}
                      end={path === '/'}
                      className={({ isActive }) =>
                        `flex items-center gap-3 px-3 py-2 rounded-md text-sm ${
                          isActive
                            ? 'bg-primary-subtle text-primary font-medium'
                            : 'hover:bg-surface-elevated text-on-surface'
                        } ${collapsed ? 'justify-center' : ''} ${isSubItem && !collapsed ? 'pl-8' : ''}`
                      }
                    >
                      <Icon className="w-5 h-5 flex-shrink-0" />
                      {!collapsed && (
                        <span className="flex items-center gap-1.5">
                          {label}
                          {badge && (
                            <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-info-subtle text-info">
                              {badge}
                            </span>
                          )}
                        </span>
                      )}
                    </NavLink>
                  )

                  return (
                    <li key={path}>
                      {collapsed ? (
                        <Tooltip content={label} side="right">
                          {navLink}
                        </Tooltip>
                      ) : (
                        navLink
                      )}
                    </li>
                  )
                })}
              </ul>
            </div>
          )
        })}
      </nav>

      <div className="border-t border-border p-2">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex items-center justify-center w-full h-9 rounded-md text-on-surface-muted hover:bg-surface-elevated hover:text-on-surface transition-colors"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? (
            <ChevronsRight className="w-5 h-5" />
          ) : (
            <ChevronsLeft className="w-5 h-5" />
          )}
        </button>
      </div>
    </aside>
  )
}
