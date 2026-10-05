import { ViswallClient } from '../client';

export class LLMAdminResource {
  constructor(private readonly client: ViswallClient) {}

  async listProviders(): Promise<unknown[]> {
    return this.client.request('GET', '/admin/llm/providers');
  }

  async createProvider(
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', '/admin/llm/providers', { data });
  }

  async getProvider(providerId: number): Promise<Record<string, unknown>> {
    return this.client.request('GET', `/admin/llm/providers/${providerId}`);
  }

  async updateProvider(
    providerId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('PATCH', `/admin/llm/providers/${providerId}`, { data });
  }

  async deleteProvider(providerId: number): Promise<void> {
    return this.client.request('DELETE', `/admin/llm/providers/${providerId}`);
  }

  async testProvider(
    providerId: number,
    model?: string,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/admin/llm/providers/${providerId}/test`, {
      data: model ? { model } : {},
    });
  }

  async discoverProviderModels(providerId: number): Promise<Record<string, unknown>> {
    return this.client.request('GET', `/admin/llm/providers/${providerId}/models/discover`);
  }

  async syncProviderModels(providerId: number): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/admin/llm/providers/${providerId}/models/sync`);
  }

  async listModels(params?: { provider_id?: number }): Promise<unknown[]> {
    return this.client.request('GET', '/admin/llm/models', { params });
  }

  async createModel(
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', '/admin/llm/models', { data });
  }

  async getModel(modelId: number): Promise<Record<string, unknown>> {
    return this.client.request('GET', `/admin/llm/models/${modelId}`);
  }

  async updateModel(
    modelId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('PATCH', `/admin/llm/models/${modelId}`, { data });
  }

  async deleteModel(modelId: number): Promise<void> {
    return this.client.request('DELETE', `/admin/llm/models/${modelId}`);
  }

  async listUseCaseConfigs(): Promise<unknown[]> {
    return this.client.request('GET', '/admin/llm/use-cases');
  }

  async createUseCaseConfig(
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', '/admin/llm/use-cases', { data });
  }

  async getUseCaseConfig(configId: number): Promise<Record<string, unknown>> {
    return this.client.request('GET', `/admin/llm/use-cases/${configId}`);
  }

  async updateUseCaseConfig(
    configId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('PATCH', `/admin/llm/use-cases/${configId}`, { data });
  }

  async deleteUseCaseConfig(configId: number): Promise<void> {
    return this.client.request('DELETE', `/admin/llm/use-cases/${configId}`);
  }
}
