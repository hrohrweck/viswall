import { ViswallClient } from '../client';

export class GroupwareResource {
  constructor(private readonly client: ViswallClient) {}

  async getStatus(domainId: number): Promise<Record<string, unknown>> {
    return this.client.request('GET', `/groupware/status/${domainId}`);
  }

  async enable(domainId: number): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/groupware/enable/${domainId}`);
  }

  async disable(domainId: number): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/groupware/disable/${domainId}`);
  }
}
