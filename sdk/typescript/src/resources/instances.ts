import { ViswallClient } from '../client';

export class InstancesResource {
  constructor(private readonly client: ViswallClient) {}

  async list(): Promise<unknown[]> {
    return this.client.request('GET', '/instances');
  }

  async create(data: Record<string, unknown>): Promise<Record<string, unknown>> {
    return this.client.request('POST', '/instances', { data });
  }

  async get(instanceId: number): Promise<Record<string, unknown>> {
    return this.client.request('GET', `/instances/${instanceId}`);
  }

  async update(instanceId: number, data: Record<string, unknown>): Promise<Record<string, unknown>> {
    return this.client.request('PATCH', `/instances/${instanceId}`, { data });
  }

  async delete(instanceId: number): Promise<void> {
    return this.client.request('DELETE', `/instances/${instanceId}`);
  }
}
