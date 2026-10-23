import { ViswallClient } from '../client';
import type { components } from '../types/generated';

/**
 * Client configuration payload returned by the admin-only
 * `GET /vpn/clients/{client_id}/config` endpoint (mirrors
 * `VPNClientConfig` in shared/schemas.py — the router declares no
 * response_model, so the OpenAPI export carries no schema for it).
 */
export interface VPNClientConfig {
  client_id: number;
  server_name: string;
  protocol: string;
  config_format: string;
  /** Base64-encoded config text (embeds the WireGuard private key). */
  config_data: string;
  filename: string;
}

export class VPNResource {
  constructor(private readonly client: ViswallClient) {}

  /**
   * List VPN servers for an instance (require_auth).
   * Plain `VPNServerResponse` — never carries `private_key`.
   */
  async listServers(
    instanceId: number,
  ): Promise<components['schemas']['VPNServerResponse'][]> {
    return this.client.request<components['schemas']['VPNServerResponse'][]>(
      'GET',
      `/vpn/servers/${instanceId}`,
    );
  }

  /**
   * Create a VPN server (require_admin).
   * Returns `VPNServerAdminResponse` — the only server shape that may
   * carry `private_key`.
   */
  async createServer(
    instanceId: number,
    data: Record<string, unknown>,
  ): Promise<components['schemas']['VPNServerAdminResponse']> {
    return this.client.request<components['schemas']['VPNServerAdminResponse']>(
      'POST',
      `/vpn/servers/${instanceId}`,
      { data },
    );
  }

  /**
   * Get VPN server by ID (require_auth).
   * Plain `VPNServerResponse` — never carries `private_key`.
   */
  async getServer(
    serverId: number,
  ): Promise<components['schemas']['VPNServerResponse']> {
    return this.client.request<components['schemas']['VPNServerResponse']>(
      'GET',
      `/vpn/servers/detail/${serverId}`,
    );
  }

  /**
   * Update a VPN server (require_admin).
   * Returns `VPNServerAdminResponse` — the only server shape that may
   * carry `private_key`.
   */
  async updateServer(
    serverId: number,
    data: Record<string, unknown>,
  ): Promise<components['schemas']['VPNServerAdminResponse']> {
    return this.client.request<components['schemas']['VPNServerAdminResponse']>(
      'PATCH',
      `/vpn/servers/${serverId}`,
      { data },
    );
  }

  async deleteServer(serverId: number): Promise<void> {
    return this.client.request('DELETE', `/vpn/servers/${serverId}`);
  }

  async startServer(serverId: number): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/vpn/servers/${serverId}/start`);
  }

  async stopServer(serverId: number): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/vpn/servers/${serverId}/stop`);
  }

  async restartServer(serverId: number): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/vpn/servers/${serverId}/restart`);
  }

  async getServerStats(serverId: number): Promise<Record<string, unknown>> {
    return this.client.request('GET', `/vpn/servers/${serverId}/stats`);
  }

  /**
   * List VPN clients for a server (require_auth).
   * Plain `VPNClientResponse` — never carries `config_file`/`config_qr`.
   */
  async listClients(
    serverId: number,
  ): Promise<components['schemas']['VPNClientResponse'][]> {
    return this.client.request<components['schemas']['VPNClientResponse'][]>(
      'GET',
      `/vpn/servers/${serverId}/clients`,
    );
  }

  /**
   * Create a VPN client (require_admin).
   * Returns `VPNClientAdminResponse` — the only client shape that carries
   * the generated `config_file`/`config_qr` (which embed the private key).
   */
  async createClient(
    serverId: number,
    data: Record<string, unknown>,
  ): Promise<components['schemas']['VPNClientAdminResponse']> {
    return this.client.request<components['schemas']['VPNClientAdminResponse']>(
      'POST',
      `/vpn/servers/${serverId}/clients`,
      { data },
    );
  }

  /**
   * Get VPN client by ID (require_auth).
   * Plain `VPNClientResponse` — never carries `config_file`/`config_qr`.
   */
  async getClient(
    clientId: number,
  ): Promise<components['schemas']['VPNClientResponse']> {
    return this.client.request<components['schemas']['VPNClientResponse']>(
      'GET',
      `/vpn/clients/${clientId}`,
    );
  }

  async updateClient(
    clientId: number,
    data: Record<string, unknown>,
  ): Promise<components['schemas']['VPNClientResponse']> {
    return this.client.request<components['schemas']['VPNClientResponse']>(
      'PATCH',
      `/vpn/clients/${clientId}`,
      { data },
    );
  }

  async deleteClient(clientId: number): Promise<void> {
    return this.client.request('DELETE', `/vpn/clients/${clientId}`);
  }

  /**
   * Download a client configuration (require_admin — the config embeds the
   * raw WireGuard private key, so the endpoint is admin-gated; a non-admin
   * call is rejected server-side with 403).
   */
  async getClientConfig(
    clientId: number,
    format: string = 'auto',
  ): Promise<VPNClientConfig> {
    return this.client.request<VPNClientConfig>(
      'GET',
      `/vpn/clients/${clientId}/config`,
      { params: { format } },
    );
  }

  async regenerateClient(clientId: number): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/vpn/clients/${clientId}/regenerate`);
  }

  async getSiteToSiteStatus(instanceId: number): Promise<unknown[]> {
    return this.client.request('GET', '/vpn/site-to-site/status', {
      params: { instance_id: instanceId },
    });
  }

  async initializeSiteToSite(
    instanceId: number,
    remoteEndpoint: string,
    remotePublicKey: string,
    options: {
      protocol?: string;
      localAddress?: string;
      allowedIps?: string;
      persistentKeepalive?: number;
    } = {},
  ): Promise<Record<string, unknown>> {
    const params: Record<string, string | number> = {
      local_instance_id: instanceId,
      remote_endpoint: remoteEndpoint,
      remote_public_key: remotePublicKey,
    };
    if (options.protocol) params.protocol = options.protocol;
    if (options.localAddress) params.local_address = options.localAddress;
    if (options.allowedIps) params.allowed_ips = options.allowedIps;
    if (options.persistentKeepalive !== undefined) {
      params.persistent_keepalive = options.persistentKeepalive;
    }
    return this.client.request('POST', '/vpn/site-to-site/initialize', {
      params,
    });
  }
}
