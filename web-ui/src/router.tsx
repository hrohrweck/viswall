import { createBrowserRouter } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Login } from './pages/Login'
import { Dashboard } from './pages/Dashboard'
import { Instances } from './pages/Instances'
import { InstanceDetail } from './pages/InstanceDetail'
import { FirewallRules } from './pages/FirewallRules'
import { NatRules } from './pages/NatRules'
import { FirewallSimulator } from './pages/Firewall/FirewallSimulator'
import { FirewallTestSuite } from './pages/Firewall/FirewallTestSuite'
import { TrafficShaping } from './pages/TrafficShaping'
import { Users } from './pages/Users'
import { Settings } from './pages/Settings'
import { Metrics } from './pages/Metrics'
import { AuditLogs } from './pages/AuditLogs'
import { RoutingRules } from './pages/RoutingRules'
import { ProtectedRoute } from './components/ProtectedRoute'
import { VPNServers } from './pages/VPN/VPNServers'
import { VPNCreate } from './pages/VPN/VPNCreate'
import { VPNServerDetail } from './pages/VPN/VPNServerDetail'
import { MailDomains } from './pages/Mail/MailDomains'
import { MailDomainCreate } from './pages/Mail/MailDomainCreate'
import { MailDomainDetail } from './pages/Mail/MailDomainDetail'
import { LLMConfiguration } from './pages/admin/LLMConfiguration'
import { DNSServers } from './pages/DNS/DNSServers'
import { DHCPServers } from './pages/DHCP/DHCPServers'

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
        path: 'routing',
        element: <RoutingRules />,
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
        path: 'firewall/nat',
        element: <NatRules />,
      },
      {
        path: 'traffic',
        element: <TrafficShaping />,
      },
      {
        path: 'vpn',
        element: <VPNServers />,
      },
      {
        path: 'dns',
        element: <DNSServers />,
      },
      {
        path: 'dhcp',
        element: <DHCPServers />,
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
        element: <Metrics />,
      },
      {
        path: 'audit',
        element: <AuditLogs />,
      },
      {
        path: 'settings',
        element: <Settings />,
      },
      {
        path: 'admin/llm',
        element: <LLMConfiguration />,
      },
    ],
  },
])
