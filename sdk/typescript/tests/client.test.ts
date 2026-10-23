import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest';
import { ViswallClient } from '../src/client';
import {
  AuthenticationError,
  NotFoundError,
  ServerError,
} from '../src/exceptions';
import { server } from './msw-setup';
import { http, HttpResponse } from 'msw';

describe('ViswallClient', () => {
  let client: ViswallClient;

  beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
  afterAll(() => server.close());
  beforeEach(() => server.resetHandlers());

  beforeEach(() => {
    client = new ViswallClient({
      baseURL: 'https://viswall.example.com',
      token: 'test-token',
    });
  });

  it('should initialize with config', () => {
    expect(client.auth).toBeDefined();
    expect(client.instances).toBeDefined();
    expect(client.firewall).toBeDefined();
    expect(client.dhcp).toBeDefined();
  });

  it('should set and clear token', () => {
    client.setToken('new-token');
    client.clearToken();
  });

  describe('AuthResource', () => {
    it('should login and return tokens', async () => {
      server.use(
        http.post('https://viswall.example.com/api/v1/auth/login', () => {
          return HttpResponse.json({
            access_token: 'abc',
            token_type: 'bearer',
          });
        }),
      );

      const result = await client.auth.login('admin', 'secret');
      expect(result).toHaveProperty('access_token');
    });

    it('should get current user', async () => {
      server.use(
        http.get('https://viswall.example.com/api/v1/auth/me', () => {
          return HttpResponse.json({
            id: 1,
            username: 'admin',
          });
        }),
      );

      const result = await client.auth.me();
      expect(result).toHaveProperty('username', 'admin');
    });
  });

  describe('InstancesResource', () => {
    it('should list instances', async () => {
      server.use(
        http.get('https://viswall.example.com/api/v1/instances', () => {
          return HttpResponse.json([{ id: 1, name: 'edge-01' }]);
        }),
      );

      const result = await client.instances.list();
      expect(Array.isArray(result)).toBe(true);
      expect(result).toHaveLength(1);
    });

    it('should create instance', async () => {
      server.use(
        http.post('https://viswall.example.com/api/v1/instances', () => {
          return HttpResponse.json({ id: 1, name: 'edge-01' });
        }),
      );

      const result = await client.instances.create({
        name: 'edge-01',
        hostname: '10.0.0.10',
      });
      expect(result).toHaveProperty('id');
    });
  });

  describe('FirewallResource', () => {
    it('should list rules', async () => {
      server.use(
        http.get('https://viswall.example.com/api/v1/firewall/rules/1', () => {
          return HttpResponse.json([{ id: 1, name: 'allow-ssh' }]);
        }),
      );

      const result = await client.firewall.listRules(1);
      expect(Array.isArray(result)).toBe(true);
    });

    it('should create rule', async () => {
      server.use(
        http.post('https://viswall.example.com/api/v1/firewall/rules/1', () => {
          return HttpResponse.json({ id: 1, name: 'allow-https' });
        }),
      );

      const result = await client.firewall.createRule(1, {
        name: 'allow-https',
        action: 'accept',
      });
      expect(result).toHaveProperty('name', 'allow-https');
    });
  });

  describe('DHCPResource', () => {
    it('should list DHCP servers', async () => {
      server.use(
        http.get('https://viswall.example.com/api/v1/dhcp/servers/1', () => {
          return HttpResponse.json([{ id: 1, name: 'kea-main' }]);
        }),
      );

      const result = await client.dhcp.listServers(1);
      expect(Array.isArray(result)).toBe(true);
      expect(result).toHaveLength(1);
    });

    it('should create DHCP subnet', async () => {
      server.use(
        http.post('https://viswall.example.com/api/v1/dhcp/servers/1/subnets', () => {
          return HttpResponse.json({ id: 10, name: 'lan-v4', type: 'v4' });
        }),
      );

      const result = await client.dhcp.createSubnet(1, {
        name: 'lan-v4',
        subnet: '192.168.10.0/24',
        type: 'v4',
      });
      expect(result).toHaveProperty('id', 10);
    });

    it('should release DHCP lease', async () => {
      server.use(
        http.delete('https://viswall.example.com/api/v1/dhcp/leases/44', () => {
          return HttpResponse.json({ id: 44, state: 'released' });
        }),
      );

      const result = await client.dhcp.releaseLease(44);
      expect(result).toHaveProperty('state', 'released');
    });
  });

  describe('MailResource', () => {
    it('should list mail aliases for a domain', async () => {
      server.use(
        http.get('https://viswall.example.com/api/v1/mail/aliases/1', () => {
          return HttpResponse.json([{ id: 7, alias: 'sales' }]);
        }),
      );

      const result = await client.mail.listAliases(1);
      expect(Array.isArray(result)).toBe(true);
      expect(result).toHaveLength(1);
    });

    it('should create a mail alias', async () => {
      server.use(
        http.post('https://viswall.example.com/api/v1/mail/aliases/1', () => {
          return HttpResponse.json({ id: 7, alias: 'sales' });
        }),
      );

      const result = await client.mail.createAlias(1, {
        alias: 'sales',
        destinations: ['user@example.com'],
      });
      expect(result).toHaveProperty('id', 7);
    });

    it('should update a mail alias', async () => {
      server.use(
        http.patch('https://viswall.example.com/api/v1/mail/aliases/7', () => {
          return HttpResponse.json({ id: 7, alias: 'sales-eu' });
        }),
      );

      const result = await client.mail.updateAlias(7, { alias: 'sales-eu' });
      expect(result).toHaveProperty('alias', 'sales-eu');
    });

    it('should delete a mail alias', async () => {
      let deleted = false;
      server.use(
        http.delete('https://viswall.example.com/api/v1/mail/aliases/7', () => {
          deleted = true;
          return HttpResponse.json({ id: 7, deleted: true });
        }),
      );

      await client.mail.deleteAlias(7);
      expect(deleted).toBe(true);
    });

    it('should update a mail domain with MTA forwarding settings', async () => {
      let received: Record<string, unknown> = {};
      server.use(
        http.patch('https://viswall.example.com/api/v1/mail/domains/4', async ({ request }) => {
          received = (await request.json()) as Record<string, unknown>;
          return HttpResponse.json({ id: 4, ...received });
        }),
      );

      const result = await client.mail.updateDomain(4, {
        mta_forward_enabled: true,
        mta_forward_host: '83.164.137.172',
        mta_forward_port: 25,
      });
      expect(received).toEqual({
        mta_forward_enabled: true,
        mta_forward_host: '83.164.137.172',
        mta_forward_port: 25,
      });
      expect(result).toHaveProperty('mta_forward_host', '83.164.137.172');
    });
  });

  describe('Error Handling', () => {
    it('should throw AuthenticationError on 401', async () => {
      server.use(
        http.get('https://viswall.example.com/api/v1/auth/me', () => {
          return HttpResponse.json({ detail: 'Unauthorized' }, { status: 401 });
        }),
      );

      await expect(client.auth.me()).rejects.toThrow(AuthenticationError);
    });

    it('should throw NotFoundError on 404', async () => {
      server.use(
        http.get('https://viswall.example.com/api/v1/instances/999', () => {
          return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
        }),
      );

      await expect(client.instances.get(999)).rejects.toThrow(NotFoundError);
    });

    it('should throw ServerError on 500', async () => {
      server.use(
        http.get('https://viswall.example.com/api/v1/instances', () => {
          return HttpResponse.json(
            { detail: 'Internal server error' },
            { status: 500 },
          );
        }),
      );

      await expect(client.instances.list()).rejects.toThrow(ServerError);
    });
  });

  describe('VPNResource site-to-site', () => {
    it('should fetch site-to-site status with instance_id param', async () => {
      server.use(
        http.get('https://viswall.example.com/api/v1/vpn/site-to-site/status', () => {
          return HttpResponse.json([
            { server_id: 3, name: 'site-to-site-base0', agent: 'online' },
          ]);
        }),
      );

      const result = await client.vpn.getSiteToSiteStatus(1);
      expect(Array.isArray(result)).toBe(true);
      expect(result).toHaveLength(1);
    });

    it('should initialize a site-to-site tunnel with query params', async () => {
      let requestUrl: URL | null = null;
      server.use(
        http.post(
          'https://viswall.example.com/api/v1/vpn/site-to-site/initialize',
          ({ request }) => {
            requestUrl = new URL(request.url);
            return HttpResponse.json({
              status: 'success',
              server_id: 3,
              message: 'initialized',
            });
          },
        ),
      );

      const result = await client.vpn.initializeSiteToSite(
        1,
        'base0.example.com:51820',
        'kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk=',
        { allowedIps: '10.80.0.0/16', persistentKeepalive: 25 },
      );

      expect(result).toHaveProperty('server_id', 3);
      expect(requestUrl).not.toBeNull();
      expect(requestUrl!.searchParams.get('local_instance_id')).toBe('1');
      expect(requestUrl!.searchParams.get('remote_endpoint')).toBe(
        'base0.example.com:51820',
      );
      expect(requestUrl!.searchParams.get('remote_public_key')).toBe(
        'kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk=',
      );
      expect(requestUrl!.searchParams.get('allowed_ips')).toBe('10.80.0.0/16');
      expect(requestUrl!.searchParams.get('persistent_keepalive')).toBe('25');
    });

    it('should regenerate client keys', async () => {
      server.use(
        http.post(
          'https://viswall.example.com/api/v1/vpn/clients/7/regenerate',
          () => {
            return HttpResponse.json({
              status: 'success',
              message: 'regenerated',
              public_key: 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb=',
            });
          },
        ),
      );

      const result = await client.vpn.regenerateClient(7);
      expect(result).toHaveProperty(
        'public_key',
        'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb=',
      );
    });
  });

  describe('VPNResource admin-only config/key shapes', () => {
    it('should list clients from the auth list endpoint (no config fields)', async () => {
      let requestUrl: URL | null = null;
      server.use(
        http.get(
          'https://viswall.example.com/api/v1/vpn/servers/1/clients',
          ({ request }) => {
            requestUrl = new URL(request.url);
            return HttpResponse.json([
              { id: 7, server_id: 1, name: 'laptop', public_key: null },
            ]);
          },
        ),
      );

      const result = await client.vpn.listClients(1);
      expect(Array.isArray(result)).toBe(true);
      expect(result).toHaveLength(1);
      expect(result[0]).toHaveProperty('name', 'laptop');
      expect(result[0]).not.toHaveProperty('config_file');
      expect(result[0]).not.toHaveProperty('config_qr');
      expect(requestUrl!.pathname).toBe('/api/v1/vpn/servers/1/clients');
    });

    it('should create a client via the admin endpoint and expose config fields', async () => {
      let requestUrl: URL | null = null;
      server.use(
        http.post(
          'https://viswall.example.com/api/v1/vpn/servers/1/clients',
          ({ request }) => {
            requestUrl = new URL(request.url);
            return HttpResponse.json({
              id: 8,
              server_id: 1,
              name: 'phone',
              public_key: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa=',
              config_file: 'W0ludGVyZmFjZV0KUHJpdmF0ZUtleSA9IHRlc3QK',
              config_qr: null,
            });
          },
        ),
      );

      const result = await client.vpn.createClient(1, { name: 'phone' });
      expect(result).toHaveProperty('config_file');
      expect(requestUrl!.pathname).toBe('/api/v1/vpn/servers/1/clients');
    });

    it('should fetch a client from the auth detail endpoint (no config fields)', async () => {
      let requestUrl: URL | null = null;
      server.use(
        http.get('https://viswall.example.com/api/v1/vpn/clients/7', ({ request }) => {
          requestUrl = new URL(request.url);
          return HttpResponse.json({ id: 7, server_id: 1, name: 'laptop' });
        }),
      );

      const result = await client.vpn.getClient(7);
      expect(result).toHaveProperty('id', 7);
      expect(result).not.toHaveProperty('config_file');
      expect(requestUrl!.pathname).toBe('/api/v1/vpn/clients/7');
    });

    it('should return plain server shapes on list/get (no private_key)', async () => {
      server.use(
        http.get('https://viswall.example.com/api/v1/vpn/servers/1', () => {
          return HttpResponse.json([{ id: 3, instance_id: 1, name: 'wg-site' }]);
        }),
        http.get(
          'https://viswall.example.com/api/v1/vpn/servers/detail/3',
          () => {
            return HttpResponse.json({ id: 3, instance_id: 1, name: 'wg-site' });
          },
        ),
      );

      const list = await client.vpn.listServers(1);
      expect(list[0]).not.toHaveProperty('private_key');
      const detail = await client.vpn.getServer(3);
      expect(detail).not.toHaveProperty('private_key');
    });

    it('should return the admin server shape on update (may carry private_key)', async () => {
      server.use(
        http.patch('https://viswall.example.com/api/v1/vpn/servers/3', () => {
          return HttpResponse.json({
            id: 3,
            instance_id: 1,
            name: 'wg-site',
            private_key: 'ccccccccccccccccccccccccccccccccccccccccccc=',
          });
        }),
      );

      const result = await client.vpn.updateServer(3, { name: 'wg-site' });
      expect(result).toHaveProperty(
        'private_key',
        'ccccccccccccccccccccccccccccccccccccccccccc=',
      );
    });

    it('should download client config from the admin endpoint with auto format', async () => {
      let requestUrl: URL | null = null;
      server.use(
        http.get(
          'https://viswall.example.com/api/v1/vpn/clients/7/config',
          ({ request }) => {
            requestUrl = new URL(request.url);
            return HttpResponse.json({
              client_id: 7,
              server_name: 'wg-site',
              protocol: 'wireguard',
              config_format: 'wg-quick',
              config_data: 'W0ludGVyZmFjZV0K',
              filename: 'laptop.wg-quick',
            });
          },
        ),
      );

      const result = await client.vpn.getClientConfig(7);
      expect(result).toHaveProperty('config_format', 'wg-quick');
      expect(requestUrl!.searchParams.get('format')).toBe('auto');
    });

    it('should surface 403 on the config endpoint to non-admins', async () => {
      server.use(
        http.get(
          'https://viswall.example.com/api/v1/vpn/clients/7/config',
          () => {
            return HttpResponse.json(
              { detail: 'Not authorized' },
              { status: 403 },
            );
          },
        ),
      );

      await expect(client.vpn.getClientConfig(7)).rejects.toThrow(
        AuthenticationError,
      );
    });
  });
});
