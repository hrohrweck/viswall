import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Server,
  Shield,
  Network,
  Mail,
  Users,
  BarChart3,
  Settings,
  Gauge,
  Route,
  ClipboardList,
} from 'lucide-react'
import { useAuthStore } from '../stores/auth'

const baseNavItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/instances', label: 'Instances', icon: Server },
  { path: '/firewall', label: 'Firewall', icon: Shield },
  { path: '/routing', label: 'Routing', icon: Route },
  { path: '/traffic', label: 'Traffic Shaping', icon: Gauge },
  { path: '/vpn', label: 'VPN', icon: Network },
  { path: '/mail', label: 'Mail', icon: Mail },
  { path: '/users', label: 'Users', icon: Users },
  { path: '/metrics', label: 'Metrics', icon: BarChart3 },
  { path: '/settings', label: 'Settings', icon: Settings },
]

export function Sidebar() {
  const { user } = useAuthStore()
  const isAdmin = user?.role === 'admin' || user?.role === 'superadmin'

  const navItems = [
    ...baseNavItems,
    ...(isAdmin ? [{ path: '/audit', label: 'Audit Logs', icon: ClipboardList }] : []),
  ]

  return (
    <aside className="w-64 bg-white border-r border-gray-200 min-h-[calc(100vh-73px)]">
      <nav className="p-4">
        <ul className="space-y-1">
          {navItems.map(({ path, label, icon: Icon }) => (
            <li key={path}>
              <NavLink
                to={path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-700 hover:bg-gray-50'
                  }`
                }
              >
                <Icon className="w-5 h-5" />
                {label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  )
}
