import { createBrowserRouter } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Login } from './pages/Login'
import { Dashboard } from './pages/Dashboard'
import { Instances } from './pages/Instances'
import { InstanceDetail } from './pages/InstanceDetail'
import { FirewallRules } from './pages/FirewallRules'
import { FirewallSimulator } from './pages/Firewall/FirewallSimulator'
import { FirewallTestSuite } from './pages/Firewall/FirewallTestSuite'
import { Users } from './pages/Users'
import { Settings } from './pages/Settings'
import { ProtectedRoute } from './components/ProtectedRoute'
import { VPNServers } from './pages/VPN/VPNServers'
import { VPNCreate } from './pages/VPN/VPNCreate'
import { VPNServerDetail } from './pages/VPN/VPNServerDetail'
import { MailDomains } from './pages/Mail/MailDomains'
import { MailDomainCreate } from './pages/Mail/MailDomainCreate'
import { MailDomainDetail } from './pages/Mail/MailDomainDetail'

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
        path: 'firewall/simulator',
        element: <FirewallSimulator />,
      },
      {
        path: 'firewall/tests',
        element: <FirewallTestSuite />,
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
        path: 'vpn/servers/:id',
        element: <VPNServerDetail />,
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
        path: 'mail/domains/:id',
        element: <MailDomainDetail />,
      },
      {
        path: 'users',
        element: <Users />,
      },
      {
        path: 'metrics',
        element: <Settings />,
      },
      {
        path: 'settings',
        element: <Settings />,
      },
    ],
  },
])
