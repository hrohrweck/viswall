import { ViswallClient } from '../client';

export class UsersResource {
  constructor(private readonly client: ViswallClient) {}

  async list(): Promise<unknown[]> {
    return this.client.request('GET', '/users');
  }

  async create(data: Record<string, unknown>): Promise<Record<string, unknown>> {
    return this.client.request('POST', '/users', { data });
  }

  async get(userId: number): Promise<Record<string, unknown>> {
    return this.client.request('GET', `/users/${userId}`);
  }

  async update(userId: number, data: Record<string, unknown>): Promise<Record<string, unknown>> {
    return this.client.request('PATCH', `/users/${userId}`, { data });
  }

  async delete(userId: number): Promise<void> {
    return this.client.request('DELETE', `/users/${userId}`);
  }
}
