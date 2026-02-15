import { createBrowserRouter } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Login } from './pages/Login'
import { Dashboard } from './pages/Dashboard'
import { Instances } from './pages/Instances'
import { InstanceDetail } from './pages/InstanceDetail'
import { FirewallRules } from './pages/FirewallRules'
import { MailDomains } from './pages/MailDomains'
import { Users } from './pages/Users'
import { Metrics } from './pages/Metrics'
import { Settings } from './pages/Settings'
import { ProtectedRoute } from './components/ProtectedRoute'

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
        path: 'mail',
        element: <MailDomains />,
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
