import { ViswallClient } from '../client';

export class AuditResource {
  constructor(private readonly client: ViswallClient) {}

  async listLogs(params?: Record<string, unknown>): Promise<unknown[]> {
    return this.client.request('GET', '/audit', { params });
  }

  async getInstanceLogs(instanceId: number, params?: Record<string, unknown>): Promise<unknown[]> {
    return this.client.request('GET', `/audit/instance/${instanceId}`, { params });
  }

  async getSummary(days?: number): Promise<Record<string, unknown>> {
    return this.client.request('GET', '/audit/summary', {
      params: days !== undefined ? { days } : undefined,
    });
  }
}
