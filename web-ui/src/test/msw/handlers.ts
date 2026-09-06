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
  // Deploy write path (final-qa e2e): the success-toast assertion needs a
  // 2xx — bypassed requests fall through to the Vite dev server (404), and
  // page.route cannot intercept fetches the worker re-issues from the
  // service-worker context.
  http.post('/api/v1/firewall/apply/:instanceId', () =>
    HttpResponse.json({ status: 'ok', deployed_rules: f.firewallRules.length }),
  ),
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
  http.get('/api/v1/mail/domains/detail/:domainId', ({ params }) => {
    const domain = f.mailDomains.find((d) => d.id === Number(params.domainId))
    return domain
      ? HttpResponse.json(domain)
      : HttpResponse.json({ detail: 'Domain not found' }, { status: 404 })
  }),
  http.get('/api/v1/mail/users/:domainId', () => HttpResponse.json(f.mailUsers)),
  http.post('/api/v1/mail/users/:domainId', async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>
    return HttpResponse.json({
      id: 99, domain_id: Number((request.url.split('/').pop()) ?? 1), username: body.username,
      full_name: body.full_name ?? null, quota_bytes: 536_870_912, quota_used: 0,
      enabled: true, forward_to: [], vacation_enabled: false,
      created_at: f.FIXED_NOW, updated_at: f.FIXED_NOW,
    })
  }),
  http.get('/api/v1/mail/messages/:domainId', () => HttpResponse.json(f.mailMessages)),
  http.post('/api/v1/mail/domains/:domainId/dkim/regenerate', () => HttpResponse.json({ status: 'ok' })),
  http.post('/api/v1/mail/messages/:messageId/reclassify', () => HttpResponse.json({ id: 1, status: 'reclassified' })),
  http.post('/api/v1/mail/messages/:messageId/action', () => HttpResponse.json({ id: 1, status: 'ok' })),
  http.get('/api/v1/groupware/status/:domainId', () => HttpResponse.json({ domain_id: 1, domain: 'example.test', groupware_enabled: true, sogo_url: 'https://sogo.example.test' })),
  http.get('/api/v1/groupware/stats/:domainId', () => HttpResponse.json({ calendars: 3, contacts: 12, active_users: 5 })),
  http.post('/api/v1/groupware/enable/:domainId', () => HttpResponse.json({ status: 'ok' })),
  http.post('/api/v1/groupware/disable/:domainId', () => HttpResponse.json({ status: 'ok' })),

  // --- LLM Admin -----------------------------------------------------------------
  http.get('/api/v1/admin/llm/providers', () => HttpResponse.json([])),
  http.get('/api/v1/admin/llm/models', () => HttpResponse.json([])),

  // --- Mail create (mutation handler) --------------------------------------------
  http.post('/api/v1/mail/domains/:instanceId', async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>
    return HttpResponse.json({
      id: 99, instance_id: 1, domain: body.domain, enabled: true,
      spam_filter_enabled: true, virus_scan_enabled: true,
      dkim_enabled: true, dmarc_enabled: true, spf_enabled: true,
      llm_enabled: false, llm_config: {}, groupware_enabled: false,
      created_at: f.FIXED_NOW, updated_at: f.FIXED_NOW,
    })
  }),
  http.delete('/api/v1/mail/domains/:domainId', () => HttpResponse.json({ status: 'ok' })),

  // --- Audit -----------------------------------------------------------------------
  http.get('/api/v1/audit/logs', () => HttpResponse.json(f.auditLogs)),
]
