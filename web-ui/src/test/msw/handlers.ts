import { http, HttpResponse } from 'msw'
import * as f from './fixtures'

/**
 * MSW request handlers for the deterministic QA fixture set.
 *
 * Paths are declared with the full `/api/v1` prefix to match the axios
 * instance (src/utils/api.ts baseURL = '/api/v1'). Path-only matching means
 * the handlers intercept requests regardless of origin, which works for the
 * browser worker (http://localhost:3000) and the node server (jsdom).
 *
 * The fixtures are READ-only: mutations (POST/PATCH/DELETE outside login) are
 * intentionally not mocked — add them per-test with server.use()/worker.use()
 * if a later todo needs to exercise a write path.
 */
export const handlers = [
  // --- Auth -------------------------------------------------------------
  http.post('/api/v1/auth/login', async ({ request }) => {
    const body = (await request.json()) as { username?: string; password?: string }
    if (body.username === f.validCredentials.username && body.password === f.validCredentials.password) {
      return HttpResponse.json(f.loginResponse)
    }
    return HttpResponse.json({ detail: 'Invalid credentials' }, { status: 401 })
  }),
  http.get('/api/v1/auth/ldap-config', () => HttpResponse.json(null)),

  // --- Instances & users -------------------------------------------------
  http.get('/api/v1/instances', () => HttpResponse.json(f.instances)),
  http.get('/api/v1/instances/:id', ({ params }) => {
    const instance = f.instances.find((i) => i.id === Number(params.id))
    return instance
      ? HttpResponse.json(instance)
      : HttpResponse.json({ detail: 'Instance not found' }, { status: 404 })
  }),
  http.get('/api/v1/users', () => HttpResponse.json(f.users)),

  // --- Metrics / dashboard ------------------------------------------------
  http.get('/api/v1/metrics/overview', () => HttpResponse.json(f.metricsOverview)),
  http.get('/api/v1/metrics/dashboard/:id', () => HttpResponse.json(f.dashboardData)),
  http.get('/api/v1/metrics/latest/:id', () => HttpResponse.json(f.latestMetric)),
  http.post('/api/v1/metrics/query', () => HttpResponse.json([f.latestMetric])),
  http.post('/api/v1/metrics/summary', () => HttpResponse.json([])),

  // --- Firewall / NAT / QoS / interfaces -----------------------------------
  http.get('/api/v1/firewall/rules/:instanceId', () => HttpResponse.json(f.firewallRules)),
  http.get('/api/v1/firewall/nat/:instanceId', () => HttpResponse.json(f.natRules)),
  http.get('/api/v1/firewall/qos/:instanceId', () => HttpResponse.json(f.qosPolicies)),
  http.get('/api/v1/firewall/interfaces/:instanceId', () => HttpResponse.json(f.networkInterfaces)),

  // --- Policy routing --------------------------------------------------------
  http.get('/api/v1/routing/rules/:instanceId', () => HttpResponse.json(f.routingRules)),

  // --- VPN -------------------------------------------------------------------
  http.get('/api/v1/vpn/protocols', () => HttpResponse.json(f.vpnProtocols)),
  http.get('/api/v1/vpn/:instanceId/servers', () => HttpResponse.json(f.vpnServers)),
  http.get('/api/v1/vpn/:instanceId/servers/:serverId', ({ params }) => {
    const server = f.vpnServers.find((s) => s.id === Number(params.serverId))
    return server
      ? HttpResponse.json(server)
      : HttpResponse.json({ detail: 'VPN server not found' }, { status: 404 })
  }),
  http.get('/api/v1/vpn/:instanceId/servers/:serverId/clients', () => HttpResponse.json(f.vpnClients)),

  // --- DNS ---------------------------------------------------------------------
  http.get('/api/v1/dns/servers/:instanceId', () => HttpResponse.json(f.dnsServers)),
  http.get('/api/v1/dns/servers/:serverId/zones', () => HttpResponse.json(f.dnsZones)),
  http.get('/api/v1/dns/zones/:zoneId/records', () => HttpResponse.json(f.dnsRecords)),

  // --- DHCP ----------------------------------------------------------------------
  http.get('/api/v1/dhcp/servers/:instanceId', () => HttpResponse.json(f.dhcpServers)),
  http.get('/api/v1/dhcp/servers/:serverId/subnets', () => HttpResponse.json(f.dhcpSubnets)),
  http.get('/api/v1/dhcp/subnets/:subnetId/pools', () => HttpResponse.json(f.dhcpPools)),
  http.get('/api/v1/dhcp/subnets/:subnetId/reservations', () => HttpResponse.json(f.dhcpReservations)),
  http.get('/api/v1/dhcp/subnets/:subnetId/options', () => HttpResponse.json(f.dhcpOptions)),
  http.get('/api/v1/dhcp/subnets/:subnetId/leases', () => HttpResponse.json(f.dhcpLeases)),
  http.get('/api/v1/dhcp/leases/active', () => HttpResponse.json(f.dhcpLeases)),

  // --- Mail -----------------------------------------------------------------------
  http.get('/api/v1/mail/domains/:instanceId', () => HttpResponse.json(f.mailDomains)),

  // --- Audit -----------------------------------------------------------------------
  http.get('/api/v1/audit/logs', () => HttpResponse.json(f.auditLogs)),
]
