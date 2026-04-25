import { ViswallClient } from '../client';

export class MailResource {
  constructor(private readonly client: ViswallClient) {}

  async listDomains(instanceId: number): Promise<unknown[]> {
    return this.client.request('GET', `/mail/domains/${instanceId}`);
  }

  async createDomain(
    instanceId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/mail/domains/${instanceId}`, { data });
  }

  async getDomain(domainId: number): Promise<Record<string, unknown>> {
    return this.client.request('GET', `/mail/domains/detail/${domainId}`);
  }

  async updateDomain(
    domainId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('PATCH', `/mail/domains/${domainId}`, { data });
  }

  async deleteDomain(domainId: number): Promise<void> {
    return this.client.request('DELETE', `/mail/domains/${domainId}`);
  }

  async listUsers(domainId: number): Promise<unknown[]> {
    return this.client.request('GET', `/mail/users/${domainId}`);
  }
}
