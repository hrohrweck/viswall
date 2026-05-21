import { ViswallClient } from '../client';

export class FirewallSimulationResource {
  constructor(private readonly client: ViswallClient) {}

  async simulateSingle(
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', '/firewall_simulation/simulate/single', { data });
  }

  async runTestSuite(
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', '/firewall_simulation/simulate/test-suite', { data });
  }

  async simulateMultiFirewall(
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', '/firewall_simulation/simulate/multi-firewall', { data });
  }

  async runMultiFirewallTests(
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', '/firewall_simulation/simulate/multi-firewall/tests', { data });
  }

  async getBasicTestSuite(): Promise<Record<string, unknown>> {
    return this.client.request('GET', '/firewall_simulation/test-suites/basic');
  }

  async getSecurityTestSuite(): Promise<Record<string, unknown>> {
    return this.client.request('GET', '/firewall_simulation/test-suites/security');
  }

  async getApplicationTestSuite(): Promise<Record<string, unknown>> {
    return this.client.request('GET', '/firewall_simulation/test-suites/application');
  }

  async getAllTestSuites(): Promise<Record<string, unknown>> {
    return this.client.request('GET', '/firewall_simulation/test-suites/all');
  }

  async getVisualSimulationData(
    data: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.client.request('POST', '/firewall_simulation/simulate/visual', { data });
  }
}
