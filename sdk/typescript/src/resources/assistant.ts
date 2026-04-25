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
}
