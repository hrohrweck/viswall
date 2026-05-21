import { ViswallClient } from '../client';

export class FirewallResource {
  constructor(private readonly client: ViswallClient) {}

  async listRules(instanceId: number): Promise<unknown[]> {
    return this.client.request('GET', `/firewall/rules/${instanceId}`);
  }

  async createRule(
    instanceId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/firewall/rules/${instanceId}`, { data });
  }

  async getRule(ruleId: number): Promise<Record<string, unknown>> {
    return this.client.request('GET', `/firewall/rules/detail/${ruleId}`);
  }

  async updateRule(
    ruleId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('PATCH', `/firewall/rules/${ruleId}`, { data });
  }

  async deleteRule(ruleId: number): Promise<void> {
    return this.client.request('DELETE', `/firewall/rules/${ruleId}`);
  }

  async applyRules(instanceId: number): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/firewall/apply/${instanceId}`);
  }

  async listInterfaces(instanceId: number): Promise<unknown[]> {
    return this.client.request('GET', `/firewall/interfaces/${instanceId}`);
  }

  async listNatRules(instanceId: number): Promise<unknown[]> {
    return this.client.request('GET', `/firewall/nat/${instanceId}`);
  }

  async createNatRule(
    instanceId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/firewall/nat/${instanceId}`, { data });
  }

  async blockIp(
    instanceId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/firewall/block/${instanceId}`, { data });
  }

  async unblockIp(
    instanceId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/firewall/unblock/${instanceId}`, { data });
  }

  async getStats(instanceId: number): Promise<Record<string, unknown>> {
    return this.client.request('GET', `/firewall/stats/${instanceId}`);
  }
}
