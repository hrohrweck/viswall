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

  async createUser(
    domainId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/mail/users/${domainId}`, { data });
  }

  async getUser(userId: number): Promise<Record<string, unknown>> {
    return this.client.request('GET', `/mail/users/detail/${userId}`);
  }

  async updateUser(
    userId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('PATCH', `/mail/users/${userId}`, { data });
  }

  async deleteUser(userId: number): Promise<void> {
    return this.client.request('DELETE', `/mail/users/${userId}`);
  }

  async getQueue(instanceId: number): Promise<Record<string, unknown>> {
    return this.client.request('GET', `/mail/queue/${instanceId}`);
  }

  async flushQueue(instanceId: number): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/mail/queue/${instanceId}/flush`);
  }

  async getStats(instanceId: number): Promise<Record<string, unknown>> {
    return this.client.request('GET', `/mail/stats/${instanceId}`);
  }

  async testClassify(
    instanceId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/mail/classify/${instanceId}`, { data });
  }

  async listMessages(
    domainId: number,
    params?: Record<string, unknown>,
  ): Promise<unknown[]> {
    return this.client.request('GET', `/mail/messages/${domainId}`, { params });
  }

  async getMessage(messageId: number): Promise<Record<string, unknown>> {
    return this.client.request('GET', `/mail/messages/detail/${messageId}`);
  }

  async reclassifyMessage(messageId: number): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/mail/messages/${messageId}/reclassify`);
  }

  async messageAction(
    messageId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/mail/messages/${messageId}/action`, { data });
  }
}
