import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import {
  ViswallAPIError,
  AuthenticationError,
  NotFoundError,
  ValidationError,
  ServerError,
  RateLimitError,
} from './exceptions';
import {
  AuthResource,
  InstancesResource,
  UsersResource,
  FirewallResource,
  RoutingResource,
  MailResource,
  MetricsResource,
  AuditResource,
  VPNResource,
  AssistantResource,
  GroupwareResource,
  DHCPResource,
} from './resources';

export interface ViswallClientConfig {
  baseURL: string;
  token?: string;
  timeout?: number;
}

export class ViswallClient {
  private readonly http: AxiosInstance;

  public readonly auth: AuthResource;
  public readonly instances: InstancesResource;
  public readonly users: UsersResource;
  public readonly firewall: FirewallResource;
  public readonly routing: RoutingResource;
  public readonly mail: MailResource;
  public readonly metrics: MetricsResource;
  public readonly audit: AuditResource;
  public readonly vpn: VPNResource;
  public readonly assistant: AssistantResource;
  public readonly groupware: GroupwareResource;
  public readonly dhcp: DHCPResource;

  constructor(config: ViswallClientConfig) {
    const baseURL = config.baseURL.replace(/\/$/, '') + '/api/v1';

    this.http = axios.create({
      baseURL,
      timeout: config.timeout ?? 30000,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
    });

    if (config.token) {
      this.http.defaults.headers.common['Authorization'] = `Bearer ${config.token}`;
    }

    this.http.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response) {
          this.handleError(error.response);
        }
        return Promise.reject(error);
      },
    );

    this.auth = new AuthResource(this);
    this.instances = new InstancesResource(this);
    this.users = new UsersResource(this);
    this.firewall = new FirewallResource(this);
    this.routing = new RoutingResource(this);
    this.mail = new MailResource(this);
    this.metrics = new MetricsResource(this);
    this.audit = new AuditResource(this);
    this.vpn = new VPNResource(this);
    this.assistant = new AssistantResource(this);
    this.groupware = new GroupwareResource(this);
    this.dhcp = new DHCPResource(this);
  }

  async request<T = unknown>(
    method: string,
    path: string,
    options?: {
      params?: Record<string, unknown>;
      data?: unknown;
    },
  ): Promise<T> {
    const config: AxiosRequestConfig = {
      method,
      url: path,
      params: options?.params,
      data: options?.data,
    };

    const response: AxiosResponse<T> = await this.http.request(config);
    return response.data;
  }

  private handleError(response: AxiosResponse): never {
    const body = response.data as Record<string, unknown> | undefined;
    const message =
      typeof body?.detail === 'string'
        ? body.detail
        : typeof body?.message === 'string'
          ? body.message
          : 'Unknown error';

    switch (response.status) {
      case 401:
      case 403:
        throw new AuthenticationError(message);
      case 404:
        throw new NotFoundError(message);
      case 422:
        throw new ValidationError(message, body);
      case 429:
        throw new RateLimitError(
          message,
          parseInt(response.headers['retry-after'] ?? '0', 10),
        );
      default:
        if (response.status >= 500) {
          throw new ServerError(message, response.status);
        }
        throw new ViswallAPIError(message, response.status, body);
    }
  }

  setToken(token: string): void {
    this.http.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  clearToken(): void {
    delete this.http.defaults.headers.common['Authorization'];
  }
}
