import { ViswallClient } from '../client';

export class MetricsResource {
  constructor(private readonly client: ViswallClient) {}

  async getLatest(instanceId: number): Promise<Record<string, unknown>> {
    return this.client.request('GET', `/metrics/latest/${instanceId}`);
  }

  async query(data: Record<string, unknown>): Promise<unknown[]> {
    return this.client.request('POST', '/metrics/query', { data });
  }

  async getDashboard(instanceId: number): Promise<Record<string, unknown>> {
    return this.client.request('GET', `/metrics/dashboard/${instanceId}`);
  }

  async getOverview(): Promise<Record<string, unknown>> {
    return this.client.request('GET', '/metrics/overview');
  }
}
