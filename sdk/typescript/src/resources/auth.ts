import { ViswallClient } from '../client';

export class AuthResource {
  constructor(private readonly client: ViswallClient) {}

  async login(username: string, password: string): Promise<Record<string, unknown>> {
    return this.client.request('POST', '/auth/login', {
      data: { username, password },
    });
  }

  async me(): Promise<Record<string, unknown>> {
    return this.client.request('GET', '/auth/me');
  }

  async refresh(): Promise<Record<string, unknown>> {
    return this.client.request('POST', '/auth/refresh');
  }

  async logout(): Promise<Record<string, unknown>> {
    return this.client.request('POST', '/auth/logout');
  }
}
