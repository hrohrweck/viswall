import { ViswallClient } from '../client';

export class DNSResource {
  constructor(private readonly client: ViswallClient) {}

  async listServers(instanceId: number): Promise<unknown[]> {
    return this.client.request('GET', `/dns/servers/${instanceId}`);
  }

  async createServer(
    instanceId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/dns/servers/${instanceId}`, { data });
  }

  async getServer(serverId: number): Promise<Record<string, unknown>> {
    return this.client.request('GET', `/dns/servers/detail/${serverId}`);
  }

  async updateServer(
    serverId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('PATCH', `/dns/servers/${serverId}`, { data });
  }

  async deleteServer(serverId: number): Promise<void> {
    return this.client.request('DELETE', `/dns/servers/${serverId}`);
  }

  async serverAction(serverId: number, action: string): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/dns/servers/${serverId}/actions/${action}`);
  }

  async listZones(serverId: number): Promise<unknown[]> {
    return this.client.request('GET', `/dns/servers/${serverId}/zones`);
  }

  async createZone(
    serverId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/dns/servers/${serverId}/zones`, { data });
  }

  async createReverseZone(
    serverId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/dns/servers/${serverId}/zones/reverse`, { data });
  }

  async getZone(zoneId: number): Promise<Record<string, unknown>> {
    return this.client.request('GET', `/dns/zones/detail/${zoneId}`);
  }

  async updateZone(
    zoneId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('PATCH', `/dns/zones/${zoneId}`, { data });
  }

  async deleteZone(zoneId: number): Promise<void> {
    return this.client.request('DELETE', `/dns/zones/${zoneId}`);
  }

  async signZone(zoneId: number): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/dns/zones/${zoneId}/sign`);
  }

  async unsignZone(zoneId: number): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/dns/zones/${zoneId}/unsign`);
  }

  async listDnssecKeys(zoneId: number): Promise<unknown[]> {
    return this.client.request('GET', `/dns/zones/${zoneId}/dnssec-keys`);
  }

  async dnssecRollover(
    zoneId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/dns/zones/${zoneId}/dnssec-rollover`, { data });
  }

  async listRecords(zoneId: number): Promise<unknown[]> {
    return this.client.request('GET', `/dns/zones/${zoneId}/records`);
  }

  async createRecord(
    zoneId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/dns/zones/${zoneId}/records`, { data });
  }

  async bulkImportRecords(
    zoneId: number,
    data: Record<string, unknown>,
  ): Promise<unknown[]> {
    return this.client.request('POST', `/dns/zones/${zoneId}/records/bulk`, { data });
  }

  async createPtrRecord(
    zoneId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/dns/zones/${zoneId}/records/ptr`, { data });
  }

  async updateRecord(
    recordId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('PATCH', `/dns/records/${recordId}`, { data });
  }

  async deleteRecord(recordId: number): Promise<void> {
    return this.client.request('DELETE', `/dns/records/${recordId}`);
  }

  async listZoneSlaves(zoneId: number): Promise<unknown[]> {
    return this.client.request('GET', `/dns/zones/${zoneId}/slaves`);
  }

  async listTsigKeys(serverId: number): Promise<unknown[]> {
    return this.client.request('GET', `/dns/servers/${serverId}/tsig-keys`);
  }

  async createTsigKey(
    serverId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/dns/servers/${serverId}/tsig-keys`, { data });
  }

  async rotateTsigKey(
    keyId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/dns/tsig-keys/${keyId}/rotate`, { data });
  }

  async deleteTsigKey(keyId: number): Promise<void> {
    return this.client.request('DELETE', `/dns/tsig-keys/${keyId}`);
  }
}
