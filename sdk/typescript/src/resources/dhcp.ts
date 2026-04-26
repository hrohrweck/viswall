import { ViswallClient } from '../client';

export class DHCPResource {
  constructor(private readonly client: ViswallClient) {}

  async listServers(instanceId: number): Promise<unknown[]> {
    return this.client.request('GET', `/dhcp/servers/${instanceId}`);
  }

  async createServer(
    instanceId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/dhcp/servers/${instanceId}`, { data });
  }

  async getServer(serverId: number): Promise<Record<string, unknown>> {
    return this.client.request('GET', `/dhcp/servers/detail/${serverId}`);
  }

  async updateServer(
    serverId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('PATCH', `/dhcp/servers/${serverId}`, { data });
  }

  async deleteServer(serverId: number): Promise<void> {
    return this.client.request('DELETE', `/dhcp/servers/${serverId}`);
  }

  async serverAction(
    serverId: number,
    action: 'start' | 'stop' | 'reload',
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/dhcp/servers/${serverId}/actions/${action}`);
  }

  async listSubnets(serverId: number): Promise<unknown[]> {
    return this.client.request('GET', `/dhcp/servers/${serverId}/subnets`);
  }

  async createSubnet(
    serverId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/dhcp/servers/${serverId}/subnets`, { data });
  }

  async getSubnet(subnetId: number): Promise<Record<string, unknown>> {
    return this.client.request('GET', `/dhcp/subnets/detail/${subnetId}`);
  }

  async updateSubnet(
    subnetId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('PATCH', `/dhcp/subnets/${subnetId}`, { data });
  }

  async deleteSubnet(subnetId: number): Promise<void> {
    return this.client.request('DELETE', `/dhcp/subnets/${subnetId}`);
  }

  async listPools(subnetId: number): Promise<unknown[]> {
    return this.client.request('GET', `/dhcp/subnets/${subnetId}/pools`);
  }

  async createPool(
    subnetId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/dhcp/subnets/${subnetId}/pools`, { data });
  }

  async deletePool(poolId: number): Promise<void> {
    return this.client.request('DELETE', `/dhcp/pools/${poolId}`);
  }

  async listReservations(subnetId: number): Promise<unknown[]> {
    return this.client.request('GET', `/dhcp/subnets/${subnetId}/reservations`);
  }

  async createReservation(
    subnetId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/dhcp/subnets/${subnetId}/reservations`, { data });
  }

  async deleteReservation(reservationId: number): Promise<void> {
    return this.client.request('DELETE', `/dhcp/reservations/${reservationId}`);
  }

  async listOptions(subnetId: number): Promise<unknown[]> {
    return this.client.request('GET', `/dhcp/subnets/${subnetId}/options`);
  }

  async createOption(
    subnetId: number,
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/dhcp/subnets/${subnetId}/options`, { data });
  }

  async deleteOption(optionId: number): Promise<void> {
    return this.client.request('DELETE', `/dhcp/options/${optionId}`);
  }

  async listSubnetLeases(subnetId: number): Promise<unknown[]> {
    return this.client.request('GET', `/dhcp/subnets/${subnetId}/leases`);
  }

  async listActiveLeases(): Promise<unknown[]> {
    return this.client.request('GET', '/dhcp/leases/active');
  }

  async releaseLease(leaseId: number): Promise<Record<string, unknown>> {
    return this.client.request('DELETE', `/dhcp/leases/${leaseId}`);
  }
}
