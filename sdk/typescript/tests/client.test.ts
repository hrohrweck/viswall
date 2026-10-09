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
});
