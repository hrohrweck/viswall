import { ViswallClient } from '../client';

export class LLMAdminResource {
  constructor(private readonly client: ViswallClient) {}

  async listProviders(): Promise<unknown[]> {
    return this.client.request('GET', '/llm_admin/providers');
  }

  async createProvider(
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', '/llm_admin/providers', { data });
  }

  async getProvider(providerId: number): Promise<Record<string, unknown>> {
    return this.client.request('GET', `/llm_admin/providers/${providerId}`);
  }

  async updateProvider(
    providerId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('PATCH', `/llm_admin/providers/${providerId}`, { data });
  }

  async deleteProvider(providerId: number): Promise<void> {
    return this.client.request('DELETE', `/llm_admin/providers/${providerId}`);
  }

  async testProvider(providerId: number): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/llm_admin/providers/${providerId}/test`);
  }

  async listModels(params?: { provider_id?: number }): Promise<unknown[]> {
    return this.client.request('GET', '/llm_admin/models', { params });
  }

  async createModel(
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', '/llm_admin/models', { data });
  }

  async getModel(modelId: number): Promise<Record<string, unknown>> {
    return this.client.request('GET', `/llm_admin/models/${modelId}`);
  }

  async updateModel(
    modelId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('PATCH', `/llm_admin/models/${modelId}`, { data });
  }

  async deleteModel(modelId: number): Promise<void> {
    return this.client.request('DELETE', `/llm_admin/models/${modelId}`);
  }

  async listUseCaseConfigs(): Promise<unknown[]> {
    return this.client.request('GET', '/llm_admin/use-cases');
  }

  async createUseCaseConfig(
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', '/llm_admin/use-cases', { data });
  }

  async getUseCaseConfig(configId: number): Promise<Record<string, unknown>> {
    return this.client.request('GET', `/llm_admin/use-cases/${configId}`);
  }

  async updateUseCaseConfig(
    configId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('PATCH', `/llm_admin/use-cases/${configId}`, { data });
  }

  async deleteUseCaseConfig(configId: number): Promise<void> {
    return this.client.request('DELETE', `/llm_admin/use-cases/${configId}`);
  }
}
