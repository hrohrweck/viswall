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
}
