export enum AuthBackend {
  LOCAL = 'local',
  LDAP = 'ldap',
  ACTIVE_DIRECTORY = 'ad',
}

export enum UserRole {
  SUPERADMIN = 'superadmin',
  ADMIN = 'admin',
  USER = 'user',
  READONLY = 'readonly',
}

export enum InstanceStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  ERROR = 'error',
  MAINTENANCE = 'maintenance',
}

export enum FirewallAction {
  ACCEPT = 'accept',
  DROP = 'drop',
  REJECT = 'reject',
}

export enum VPNProtocol {
  WIREGUARD = 'wireguard',
  IPSEC = 'ipsec',
  OPENVPN = 'openvpn',
  PPTP = 'pptp',
  L2TP = 'l2tp',
}

export enum VPNStatus {
  RUNNING = 'running',
  STOPPED = 'stopped',
  ERROR = 'error',
  RESTARTING = 'restarting',
}

export enum VPNClientType {
  USER = 'user',
  SITE = 'site',
  SERVICE = 'service',
}

export enum VPNAuthType {
  CERT = 'cert',
  PASSWORD = 'password',
  SSO = 'sso',
  PSK = 'psk',
  PUBLIC_KEY = 'public_key',
}

export interface Instance {
  id: number;
  name: string;
  hostname: string;
  capabilities: string[];
  api_endpoint: string;
  status: InstanceStatus;
  last_seen: string | null;
  config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface InstanceCreate {
  name: string;
  hostname: string;
  capabilities?: string[];
  api_key?: string;
}

export interface InstanceUpdate {
  name?: string;
  hostname?: string;
  status?: InstanceStatus;
  capabilities?: string[];
  config?: Record<string, unknown>;
}

export interface User {
  id: number;
  username: string;
  email: string;
  auth_backend: AuthBackend;
  role: UserRole;
  is_active: boolean;
  instances: number[];
  preferences: Record<string, unknown>;
  last_login: string | null;
  created_at: string;
  updated_at: string;
}

export interface UserCreate {
  username: string;
  email: string;
  password?: string;
  auth_backend?: AuthBackend;
  role?: UserRole;
  instances?: number[];
}

export interface UserUpdate {
  email?: string;
  role?: UserRole;
  is_active?: boolean;
  instances?: number[];
  preferences?: Record<string, unknown>;
}

export interface UserPasswordChange {
  current_password: string;
  new_password: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface FirewallRule {
  id: number;
  instance_id: number;
  name: string;
  description: string | null;
  enabled: boolean;
  source_type: string;
  source_value: string | null;
  dest_type: string;
  dest_value: string | null;
  service_protocol: string;
  service_ports: string | null;
  action: FirewallAction;
  log_enabled: boolean;
  order_index: number;
  created_by: number | null;
  created_at: string;
  updated_at: string;
}

export interface FirewallRuleCreate {
  name: string;
  description?: string;
  enabled?: boolean;
  source_type?: string;
  source_value?: string;
  dest_type?: string;
  dest_value?: string;
  service_protocol?: string;
  service_ports?: string;
  action?: FirewallAction;
  log_enabled?: boolean;
}

export interface FirewallRuleUpdate {
  name?: string;
  description?: string;
  enabled?: boolean;
  source_type?: string;
  source_value?: string;
  dest_type?: string;
  dest_value?: string;
  service_protocol?: string;
  service_ports?: string;
  action?: FirewallAction;
  log_enabled?: boolean;
}

export interface NetworkInterface {
  id: number;
  instance_id: number;
  name: string;
  type: string;
  config_type: string;
  ip_address: string | null;
  netmask: string | null;
  gateway: string | null;
  bandwidth_in: number | null;
  bandwidth_out: number | null;
  enabled: boolean;
  updated_at: string;
}

export interface MailDomain {
  id: number;
  instance_id: number;
  domain: string;
  enabled: boolean;
  spam_filter_enabled: boolean;
  virus_scan_enabled: boolean;
  dkim_enabled: boolean;
  dmarc_enabled: boolean;
  spf_enabled: boolean;
  llm_enabled: boolean;
  llm_config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface MailDomainCreate {
  domain: string;
  enabled?: boolean;
  spam_filter_enabled?: boolean;
  virus_scan_enabled?: boolean;
  dkim_enabled?: boolean;
  dmarc_enabled?: boolean;
  spf_enabled?: boolean;
  llm_enabled?: boolean;
  llm_config?: Record<string, unknown>;
}

export interface MailDomainUpdate {
  enabled?: boolean;
  spam_filter_enabled?: boolean;
  virus_scan_enabled?: boolean;
  dkim_enabled?: boolean;
  dmarc_enabled?: boolean;
  spf_enabled?: boolean;
  llm_enabled?: boolean;
  llm_config?: Record<string, unknown>;
}

export interface MailUser {
  id: number;
  domain_id: number;
  username: string;
  full_name: string | null;
  quota_bytes: number;
  quota_used: number;
  enabled: boolean;
  forward_to: string[];
  vacation_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface MailUserCreate {
  username: string;
  full_name?: string;
  password?: string;
  quota_bytes?: number;
  enabled?: boolean;
  forward_to?: string[];
}

export interface MailUserUpdate {
  full_name?: string;
  password?: string;
  quota_bytes?: number;
  enabled?: boolean;
  forward_to?: string[];
  vacation_enabled?: boolean;
  vacation_message?: string;
}

export interface VPNServer {
  id: number;
  instance_id: number;
  name: string;
  description: string | null;
  enabled: boolean;
  protocol: VPNProtocol;
  listen_address: string;
  listen_port: number | null;
  network_cidr: string;
  dns_servers: string[];
  push_routes: string[];
  internet_redirect: boolean;
  status: VPNStatus;
  config: Record<string, unknown>;
  connected_clients: number;
  bytes_received: number;
  bytes_sent: number;
  created_by: number | null;
  created_at: string;
  updated_at: string;
}

export interface VPNServerCreate {
  name: string;
  description?: string;
  enabled?: boolean;
  protocol: VPNProtocol;
  listen_address?: string;
  listen_port?: number;
  network_cidr?: string;
  dns_servers?: string[];
  push_routes?: string[];
  internet_redirect?: boolean;
  wireguard_config?: WireGuardConfig;
  ipsec_config?: IPSecConfig;
  openvpn_config?: OpenVPNConfig;
  l2tp_config?: L2TPConfig;
  pptp_config?: PPTPConfig;
}

export interface VPNServerUpdate {
  name?: string;
  description?: string;
  enabled?: boolean;
  listen_address?: string;
  listen_port?: number;
  network_cidr?: string;
  dns_servers?: string[];
  push_routes?: string[];
  internet_redirect?: boolean;
  config?: Record<string, unknown>;
}

export interface WireGuardConfig {
  private_key?: string;
  public_key?: string;
  listen_port?: number;
  network_cidr?: string;
  post_up?: string;
  post_down?: string;
  mtu?: number;
}

export interface IPSecConfig {
  tunnel_type?: string;
  ike_encryption?: string;
  ike_integrity?: string;
  ike_dh_group?: string;
  ike_lifetime?: number;
  esp_encryption?: string;
  esp_integrity?: string;
  esp_dh_group?: string;
  esp_lifetime?: number;
  auth_method?: string;
  dpd_enabled?: boolean;
  dpd_interval?: number;
  dpd_timeout?: number;
  mobike?: boolean;
}

export interface OpenVPNConfig {
  mode?: string;
  topology?: string;
  cipher?: string;
  auth_digest?: string;
  tls_version_min?: string;
  tls_cipher?: string;
  protocol?: string;
  port?: number;
  compression?: string | null;
  fast_io?: boolean;
  duplicate_cn?: boolean;
  client_to_client?: boolean;
  max_clients?: number;
  keepalive_interval?: number;
  keepalive_timeout?: number;
}

export interface L2TPConfig {
  ppp_interface?: string;
  ppp_options?: string[];
  ipsec_psk?: string;
  chap_secrets?: boolean;
  ms_dns?: string[];
}

export interface PPTPConfig {
  ppp_interface?: string;
  require_mppe?: boolean;
  ms_dns?: string[];
}

export interface VPNClient {
  id: number;
  server_id: number;
  user_id: number | null;
  name: string;
  description: string | null;
  enabled: boolean;
  client_type: VPNClientType;
  auth_type: VPNAuthType;
  assigned_ip: string | null;
  allowed_ips: string[];
  push_routes_override: string[];
  last_connected: string | null;
  last_ip: string | null;
  connection_count: number;
  bytes_received: number;
  bytes_sent: number;
  public_key: string | null;
  config_qr: string | null;
  config_file: string | null;
  created_at: string;
  updated_at: string;
}

export interface VPNClientCreate {
  name: string;
  description?: string;
  enabled?: boolean;
  client_type?: VPNClientType;
  auth_type?: VPNAuthType;
  assigned_ip?: string;
  allowed_ips?: string[];
  push_routes_override?: string[];
  user_id?: number;
  generate_qr?: boolean;
}

export interface VPNClientUpdate {
  name?: string;
  description?: string;
  enabled?: boolean;
  assigned_ip?: string;
  allowed_ips?: string[];
  push_routes_override?: string[];
}

export interface VPNConnection {
  id: number;
  server_id: number;
  client_id: number;
  client_name: string;
  protocol: VPNProtocol;
  client_ip: string;
  virtual_ip: string;
  connected_at: string;
  bytes_received: number;
  bytes_sent: number;
  status: string;
}

export interface VPNProtocolRecommendation {
  protocol: VPNProtocol;
  priority: number;
  security_score: number;
  performance_score: number;
  compatibility_score: number;
  description: string;
  use_cases: string[];
}

export interface AuditLog {
  id: number;
  user_id: number | null;
  instance_id: number | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  old_value: Record<string, unknown> | null;
  new_value: Record<string, unknown> | null;
  ip_address: string | null;
  timestamp: string;
}

export interface LLMConfig {
  provider: string;
  model: string;
  api_key?: string;
  api_base?: string;
  temperature: number;
  max_tokens: number;
  system_prompt: string;
  auto_classify: boolean;
  confidence_threshold: number;
  categories: string[];
}

export interface AssistantMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface AssistantResponse {
  response: string;
  type?: string;
  data?: Record<string, unknown>;
  suggestions?: string[];
}

export interface SimulationRequest {
  rules: FirewallRule[];
  packet: {
    src_ip: string;
    dst_ip: string;
    protocol: string;
    src_port?: number;
    dst_port?: number;
    interface_in?: string;
    interface_out?: string;
    state?: string;
  };
}

export interface SimulationResult {
  action: FirewallAction;
  matched_rule: number | null;
  matched_rule_name: string | null;
  trace: Array<{
    rule_id: number;
    rule_name: string;
    matched: boolean;
    reason: string;
  }>;
}

export interface TestSuiteRequest {
  rules: FirewallRule[];
  test_cases: Array<{
    name: string;
    packet: SimulationRequest['packet'];
    expected_action: FirewallAction;
  }>;
}

export interface TestSuiteResult {
  total: number;
  passed: number;
  failed: number;
  results: Array<{
    name: string;
    passed: boolean;
    expected: FirewallAction;
    actual: FirewallAction;
    details: string;
  }>;
}

export interface ApiError {
  detail: string;
}
