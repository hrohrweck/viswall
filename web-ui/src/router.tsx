import { createBrowserRouter } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Login } from './pages/Login'
import { Dashboard } from './pages/Dashboard'
import { Instances } from './pages/Instances'
import { InstanceDetail } from './pages/InstanceDetail'
import { FirewallRules } from './pages/FirewallRules'
import { Users } from './pages/Users'
import { Metrics } from './pages/Metrics'
import { Settings } from './pages/Settings'
import { ProtectedRoute } from './components/ProtectedRoute'
import { VPNServers } from './pages/VPN/VPNServers'
import { VPNCreate } from './pages/VPN/VPNCreate'
import { MailDomains } from './pages/Mail/MailDomains'
import { MailDomainCreate } from './pages/Mail/MailDomainCreate'

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <Layout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <Dashboard />,
      },
      {
        path: 'instances',
        element: <Instances />,
      },
      {
        path: 'instances/:id',
        element: <InstanceDetail />,
      },
      {
        path: 'firewall',
        element: <FirewallRules />,
      },
      {
        path: 'vpn',
        element: <VPNServers />,
      },
      {
        path: 'vpn/create',
        element: <VPNCreate />,
      },
      {
        path: 'mail',
        element: <MailDomains />,
      },
      {
        path: 'mail/domains/create',
        element: <MailDomainCreate />,
      },
      {
        path: 'users',
        element: <Users />,
      },
      {
        path: 'metrics',
        element: <Metrics />,
      },
      {
        path: 'settings',
        element: <Settings />,
      },
    ],
  },
])
