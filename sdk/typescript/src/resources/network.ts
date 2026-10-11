import { ViswallClient } from '../client';

export class NetworkResource {
  constructor(private readonly client: ViswallClient) {}

  async listInterfaces(instanceId: number): Promise<unknown[]> {
    return this.client.request('GET', `/network/interfaces/${instanceId}`);
  }

  async createInterface(
    instanceId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/network/interfaces/${instanceId}`, { data });
  }

  async updateInterface(
    interfaceId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('PATCH', `/network/interfaces/detail/${interfaceId}`, { data });
  }

  async deleteInterface(interfaceId: number): Promise<void> {
    return this.client.request('DELETE', `/network/interfaces/detail/${interfaceId}`);
  }

  async liveInterfaces(instanceId: number): Promise<Record<string, unknown>> {
    return this.client.request('GET', `/network/interfaces/${instanceId}/live`);
  }

  async applyInterfaces(
    instanceId: number,
    options: { force?: boolean } = {},
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/network/interfaces/${instanceId}/apply`, {
      data: { force: options.force ?? false },
    });
  }
}
