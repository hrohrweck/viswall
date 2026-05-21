import { ViswallClient } from '../client';

export class AssistantResource {
  constructor(private readonly client: ViswallClient) {}

  async chat(message: string): Promise<Record<string, unknown>> {
    return this.client.request('POST', '/assistant/chat', {
      data: { message },
    });
  }

  async getStatus(): Promise<Record<string, unknown>> {
    return this.client.request('GET', '/assistant/status');
  }

  async suggestFirewallRule(
    instanceId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/assistant/suggest-rule/${instanceId}`, { data });
  }

  async generateTests(
    instanceId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/assistant/generate-tests/${instanceId}`, { data });
  }

  async explainConfiguration(
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', '/assistant/explain', { data });
  }

  async securityAudit(
    instanceId: number,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/assistant/security-audit/${instanceId}`);
  }

  async getCapabilities(): Promise<Record<string, unknown>> {
    return this.client.request('GET', '/assistant/capabilities');
  }

  async getConfig(): Promise<Record<string, unknown>> {
    return this.client.request('GET', '/assistant/config');
  }

  async updateConfig(
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('PATCH', '/assistant/config', { data });
  }
}
