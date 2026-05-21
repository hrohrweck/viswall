import { ViswallClient } from '../client';

export class VPNResource {
  constructor(private readonly client: ViswallClient) {}

  async listServers(instanceId: number): Promise<unknown[]> {
    return this.client.request('GET', `/vpn/servers/${instanceId}`);
  }

  async createServer(
    instanceId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/vpn/servers/${instanceId}`, { data });
  }

  async getServer(serverId: number): Promise<Record<string, unknown>> {
    return this.client.request('GET', `/vpn/servers/detail/${serverId}`);
  }

  async updateServer(
    serverId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('PATCH', `/vpn/servers/${serverId}`, { data });
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

  async listClients(serverId: number): Promise<unknown[]> {
    return this.client.request('GET', `/vpn/clients/${serverId}`);
  }

  async createClient(
    serverId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/vpn/clients/${serverId}`, { data });
  }

  async getClient(clientId: number): Promise<Record<string, unknown>> {
    return this.client.request('GET', `/vpn/clients/detail/${clientId}`);
  }

  async updateClient(
    clientId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('PATCH', `/vpn/clients/${clientId}`, { data });
  }

  async deleteClient(clientId: number): Promise<void> {
    return this.client.request('DELETE', `/vpn/clients/${clientId}`);
  }

  async getClientConfig(clientId: number): Promise<Record<string, unknown>> {
    return this.client.request('GET', `/vpn/clients/${clientId}/config`);
  }

  async regenerateClient(clientId: number): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/vpn/clients/${clientId}/regenerate`);
  }
}
