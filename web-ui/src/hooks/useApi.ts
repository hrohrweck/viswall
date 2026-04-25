import {
  useQuery,
  useMutation,
  useQueryClient,
  UseQueryOptions,
} from '@tanstack/react-query'
import { api } from '../utils/api'
import type {
  Instance,
  InstanceCreate,
  InstanceUpdate,
  User,
  UserCreate,
  UserUpdate,
  UserPasswordChange,
  LoginRequest,
  LoginResponse,
  FirewallRule,
  FirewallRuleCreate,
  FirewallRuleUpdate,
  NetworkInterface,
  MailDomain,
  MailDomainCreate,
  MailDomainUpdate,
  MailUser,
  MailUserCreate,
  MailUserUpdate,
  VPNServer,
  VPNServerCreate,
  VPNServerUpdate,
  VPNClient,
  VPNClientCreate,
  VPNClientUpdate,
  VPNProtocolRecommendation,
  SimulationRequest,
  SimulationResult,
  TestSuiteRequest,
  TestSuiteResult,
  AssistantMessage,
  AssistantResponse,
  AuditLog,
  MetricSnapshot,
  MetricsQuery,
  MetricsSummary,
  DashboardData,
  RoutingRule,
  RoutingRuleCreate,
  RoutingRuleUpdate,
  LLMConfig,
  LLMProvider,
  LLMProviderCreate,
  LLMProviderUpdate,
  LLMModel,
  LLMModelCreate,
  LLMModelUpdate,
  LLMUseCaseConfig,
  LLMUseCaseConfigUpdate,
  LDAPConfig,
  MailMessage,
  CategoryConfig,
} from '../types'

const queryKeys = {
  instances: ['instances'] as const,
  instance: (id: number) => ['instances', id] as const,
  users: ['users'] as const,
  user: (id: number) => ['users', id] as const,
  firewallRules: (instanceId: number) => ['firewall-rules', instanceId] as const,
  networkInterfaces: (instanceId: number) => ['network-interfaces', instanceId] as const,
  mailDomains: (instanceId: number) => ['mail-domains', instanceId] as const,
  mailDomain: (instanceId: number, domainId: number) => ['mail-domains', instanceId, domainId] as const,
  mailUsers: (instanceId: number, domainId: number) => ['mail-users', instanceId, domainId] as const,
  mailMessages: (domainId: number, filters?: Record<string, unknown>) => ['mail-messages', domainId, filters] as const,
  mailMessage: (messageId: number) => ['mail-message', messageId] as const,
  vpnServers: (instanceId: number) => ['vpn-servers', instanceId] as const,
  vpnServer: (instanceId: number, serverId: number) => ['vpn-servers', instanceId, serverId] as const,
  vpnClients: (instanceId: number, serverId: number) => ['vpn-clients', instanceId, serverId] as const,
  vpnProtocols: ['vpn-protocols'] as const,
  auditLogs: (params?: Record<string, unknown>) => ['audit-logs', params] as const,
  metricsLatest: (instanceId: number) => ['metrics', 'latest', instanceId] as const,
  metricsQuery: (params?: Record<string, unknown>) => ['metrics', 'query', params] as const,
  metricsSummary: (params?: Record<string, unknown>) => ['metrics', 'summary', params] as const,
  dashboardData: (instanceId: number) => ['dashboard', instanceId] as const,
  metricsOverview: ['metrics', 'overview'] as const,
  routingRules: (instanceId: number) => ['routing-rules', instanceId] as const,
  llmProviders: ['llm-providers'] as const,
  llmProvider: (id: number) => ['llm-providers', id] as const,
  llmModels: (providerId?: number) => ['llm-models', providerId] as const,
  llmModel: (id: number) => ['llm-models', id] as const,
  llmUseCaseConfigs: ['llm-use-case-configs'] as const,
}

export { queryKeys }

export function useInstances(options?: Partial<UseQueryOptions<Instance[]>>) {
  return useQuery<Instance[]>({
    queryKey: queryKeys.instances,
    queryFn: async () => {
      const { data } = await api.get('/instances')
      return data
    },
    ...options,
  })
}

export function useInstance(id: number, options?: Partial<UseQueryOptions<Instance>>) {
  return useQuery<Instance>({
    queryKey: queryKeys.instance(id),
    queryFn: async () => {
      const { data } = await api.get(`/instances/${id}`)
      return data
    },
    enabled: !!id,
    ...options,
  })
}

export function useCreateInstance() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: InstanceCreate) => {
      const { data } = await api.post('/instances', body)
      return data as Instance
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.instances })
    },
  })
}

export function useUpdateInstance() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, ...body }: InstanceUpdate & { id: number }) => {
      const { data } = await api.patch(`/instances/${id}`, body)
      return data as Instance
    },
    onSuccess: (_, variables) => {
      qc.invalidateQueries({ queryKey: queryKeys.instances })
      qc.invalidateQueries({ queryKey: queryKeys.instance(variables.id) })
    },
  })
}

export function useDeleteInstance() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/instances/${id}`)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.instances })
    },
  })
}

export function useUsers() {
  return useQuery<User[]>({
    queryKey: queryKeys.users,
    queryFn: async () => {
      const { data } = await api.get('/users')
      return data
    },
  })
}

export function useUser(id: number) {
  return useQuery<User>({
    queryKey: queryKeys.user(id),
    queryFn: async () => {
      const { data } = await api.get(`/users/${id}`)
      return data
    },
    enabled: !!id,
  })
}

export function useCreateUser() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: UserCreate) => {
      const { data } = await api.post('/users', body)
      return data as User
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.users })
    },
  })
}

export function useUpdateUser() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, ...body }: UserUpdate & { id: number }) => {
      const { data } = await api.patch(`/users/${id}`, body)
      return data as User
    },
    onSuccess: (_, variables) => {
      qc.invalidateQueries({ queryKey: queryKeys.users })
      qc.invalidateQueries({ queryKey: queryKeys.user(variables.id) })
    },
  })
}

export function useDeleteUser() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/users/${id}`)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.users })
    },
  })
}

export function useChangePassword() {
  return useMutation({
    mutationFn: async ({ id, ...body }: UserPasswordChange & { id: number }) => {
      await api.post(`/users/${id}/change-password`, body)
    },
  })
}

export function useLogin() {
  return useMutation({
    mutationFn: async (body: LoginRequest) => {
      const { data } = await api.post<LoginResponse>('/auth/login', body)
      return data
    },
  })
}

export function useFirewallRules(instanceId: number, chain?: string) {
  return useQuery<FirewallRule[]>({
    queryKey: [...queryKeys.firewallRules(instanceId), chain],
    queryFn: async () => {
      const params = chain ? { chain } : {}
      const { data } = await api.get(`/firewall/rules/${instanceId}`, { params })
      return data
    },
    enabled: !!instanceId,
  })
}

export function useCreateFirewallRule(instanceId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: FirewallRuleCreate) => {
      const { data } = await api.post(`/firewall/rules/${instanceId}`, body)
      return data as FirewallRule
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.firewallRules(instanceId) })
    },
  })
}

export function useUpdateFirewallRule(instanceId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, ...body }: FirewallRuleUpdate & { id: number }) => {
      const { data } = await api.patch(`/firewall/rules/${instanceId}/${id}`, body)
      return data as FirewallRule
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.firewallRules(instanceId) })
    },
  })
}

export function useDeleteFirewallRule(instanceId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (ruleId: number) => {
      await api.delete(`/firewall/rules/${instanceId}/${ruleId}`)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.firewallRules(instanceId) })
    },
  })
}

export function useReorderFirewallRule(instanceId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ ruleId, direction }: { ruleId: number; direction: 'up' | 'down' }) => {
      await api.post(`/firewall/rules/${instanceId}/reorder/${ruleId}/${direction}`)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.firewallRules(instanceId) })
    },
  })
}

export function useNetworkInterfaces(instanceId: number) {
  return useQuery<NetworkInterface[]>({
    queryKey: queryKeys.networkInterfaces(instanceId),
    queryFn: async () => {
      const { data } = await api.get(`/firewall/interfaces/${instanceId}`)
      return data
    },
    enabled: !!instanceId,
  })
}

export function useDeployFirewall(instanceId: number) {
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post(`/firewall/deploy/${instanceId}`)
      return data
    },
  })
}

export function useMailDomains(instanceId: number) {
  return useQuery<MailDomain[]>({
    queryKey: queryKeys.mailDomains(instanceId),
    queryFn: async () => {
      const { data } = await api.get(`/mail/${instanceId}/domains`)
      return data
    },
    enabled: !!instanceId,
  })
}

export function useMailDomain(instanceId: number, domainId: number) {
  return useQuery<MailDomain>({
    queryKey: queryKeys.mailDomain(instanceId, domainId),
    queryFn: async () => {
      const { data } = await api.get(`/mail/${instanceId}/domains/${domainId}`)
      return data
    },
    enabled: !!instanceId && !!domainId,
  })
}

export function useCreateMailDomain(instanceId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: MailDomainCreate) => {
      const { data } = await api.post(`/mail/${instanceId}/domains`, body)
      return data as MailDomain
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.mailDomains(instanceId) })
    },
  })
}

export function useUpdateMailDomain(instanceId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, ...body }: MailDomainUpdate & { id: number }) => {
      const { data } = await api.patch(`/mail/${instanceId}/domains/${id}`, body)
      return data as MailDomain
    },
    onSuccess: (_, variables) => {
      qc.invalidateQueries({ queryKey: queryKeys.mailDomains(instanceId) })
      qc.invalidateQueries({ queryKey: queryKeys.mailDomain(instanceId, variables.id) })
    },
  })
}

export function useDeleteMailDomain(instanceId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (domainId: number) => {
      await api.delete(`/mail/${instanceId}/domains/${domainId}`)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.mailDomains(instanceId) })
    },
  })
}

export function useMailMessages(domainId: number, filters?: Record<string, unknown>) {
  return useQuery<MailMessage[]>({
    queryKey: queryKeys.mailMessages(domainId, filters),
    queryFn: async () => {
      const { data } = await api.get(`/mail/messages/${domainId}`, { params: filters })
      return data
    },
    enabled: !!domainId,
  })
}

export function useMailMessage(messageId: number) {
  return useQuery<MailMessage>({
    queryKey: queryKeys.mailMessage(messageId),
    queryFn: async () => {
      const { data } = await api.get(`/mail/messages/detail/${messageId}`)
      return data
    },
    enabled: !!messageId,
  })
}

export function useClassifyEmail(domainId: number) {
  return useMutation({
    mutationFn: async (testData: { subject: string; sender: string; body_preview?: string }) => {
      const { data } = await api.post(`/mail/domains/${domainId}/classify`, testData)
      return data as { category: string; confidence: number; reason: string; action: string }
    },
  })
}

export function useReclassifyMessage(messageId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post(`/mail/messages/${messageId}/reclassify`)
      return data as MailMessage
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.mailMessage(messageId) })
    },
  })
}

export function useMessageAction(messageId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ action, reason }: { action: string; reason?: string }) => {
      const { data } = await api.post(`/mail/messages/${messageId}/action`, { action, reason })
      return data as MailMessage
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.mailMessage(messageId) })
    },
  })
}

export function useMailUsers(instanceId: number, domainId: number) {
  return useQuery<MailUser[]>({
    queryKey: queryKeys.mailUsers(instanceId, domainId),
    queryFn: async () => {
      const { data } = await api.get(`/mail/${instanceId}/domains/${domainId}/users`)
      return data
    },
    enabled: !!instanceId && !!domainId,
  })
}

export function useCreateMailUser(instanceId: number, domainId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: MailUserCreate) => {
      const { data } = await api.post(`/mail/${instanceId}/domains/${domainId}/users`, body)
      return data as MailUser
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.mailUsers(instanceId, domainId) })
    },
  })
}

export function useUpdateMailUser(instanceId: number, domainId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, ...body }: MailUserUpdate & { id: number }) => {
      const { data } = await api.patch(`/mail/${instanceId}/domains/${domainId}/users/${id}`, body)
      return data as MailUser
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.mailUsers(instanceId, domainId) })
    },
  })
}

export function useDeleteMailUser(instanceId: number, domainId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (userId: number) => {
      await api.delete(`/mail/${instanceId}/domains/${domainId}/users/${userId}`)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.mailUsers(instanceId, domainId) })
    },
  })
}

export function useRegenerateDkim(instanceId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (domainId: number) => {
      const { data } = await api.post(`/mail/${instanceId}/domains/${domainId}/regenerate-dkim`)
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.mailDomains(instanceId) })
    },
  })
}

export function useVPNServers(instanceId: number) {
  return useQuery<VPNServer[]>({
    queryKey: queryKeys.vpnServers(instanceId),
    queryFn: async () => {
      const { data } = await api.get(`/vpn/${instanceId}/servers`)
      return data
    },
    enabled: !!instanceId,
  })
}

export function useVPNServer(instanceId: number, serverId: number) {
  return useQuery<VPNServer>({
    queryKey: queryKeys.vpnServer(instanceId, serverId),
    queryFn: async () => {
      const { data } = await api.get(`/vpn/${instanceId}/servers/${serverId}`)
      return data
    },
    enabled: !!instanceId && !!serverId,
  })
}

export function useVPNProtocols() {
  return useQuery<VPNProtocolRecommendation[]>({
    queryKey: queryKeys.vpnProtocols,
    queryFn: async () => {
      const { data } = await api.get('/vpn/protocols')
      return data
    },
  })
}

export function useCreateVPNServer(instanceId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: VPNServerCreate) => {
      const { data } = await api.post(`/vpn/${instanceId}/servers`, body)
      return data as VPNServer
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.vpnServers(instanceId) })
    },
  })
}

export function useUpdateVPNServer(instanceId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, ...body }: VPNServerUpdate & { id: number }) => {
      const { data } = await api.patch(`/vpn/${instanceId}/servers/${id}`, body)
      return data as VPNServer
    },
    onSuccess: (_, variables) => {
      qc.invalidateQueries({ queryKey: queryKeys.vpnServers(instanceId) })
      qc.invalidateQueries({ queryKey: queryKeys.vpnServer(instanceId, variables.id) })
    },
  })
}

export function useDeleteVPNServer(instanceId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (serverId: number) => {
      await api.delete(`/vpn/${instanceId}/servers/${serverId}`)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.vpnServers(instanceId) })
    },
  })
}

export function useVPNClients(instanceId: number, serverId: number) {
  return useQuery<VPNClient[]>({
    queryKey: queryKeys.vpnClients(instanceId, serverId),
    queryFn: async () => {
      const { data } = await api.get(`/vpn/${instanceId}/servers/${serverId}/clients`)
      return data
    },
    enabled: !!instanceId && !!serverId,
  })
}

export function useCreateVPNClient(instanceId: number, serverId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (body: VPNClientCreate) => {
      const { data } = await api.post(`/vpn/${instanceId}/servers/${serverId}/clients`, body)
      return data as VPNClient
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.vpnClients(instanceId, serverId) })
    },
  })
}

export function useUpdateVPNClient(instanceId: number, serverId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, ...body }: VPNClientUpdate & { id: number }) => {
      const { data } = await api.patch(`/vpn/${instanceId}/servers/${serverId}/clients/${id}`, body)
      return data as VPNClient
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.vpnClients(instanceId, serverId) })
    },
  })
}

export function useDeleteVPNClient(instanceId: number, serverId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (clientId: number) => {
      await api.delete(`/vpn/${instanceId}/servers/${serverId}/clients/${clientId}`)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.vpnClients(instanceId, serverId) })
    },
  })
}

export function useVPNServerAction(instanceId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ serverId, action }: { serverId: number; action: 'start' | 'stop' | 'restart' }) => {
      const { data } = await api.post(`/vpn/${instanceId}/servers/${serverId}/${action}`)
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.vpnServers(instanceId) })
    },
  })
}

export function useSimulatePacket() {
  return useMutation({
    mutationFn: async (body: SimulationRequest) => {
      const { data } = await api.post('/simulation/single', body)
      return data as SimulationResult
    },
  })
}

export function useRunTestSuite() {
  return useMutation({
    mutationFn: async (body: TestSuiteRequest) => {
      const { data } = await api.post('/simulation/test-suite', body)
      return data as TestSuiteResult
    },
  })
}

export function useAssistantChat() {
  return useMutation({
    mutationFn: async (messages: AssistantMessage[]) => {
      const { data } = await api.post('/assistant/chat', { messages })
      return data as AssistantResponse
    },
  })
}

export function useAssistantRuleSuggestion() {
  return useMutation({
    mutationFn: async (description: string) => {
      const { data } = await api.post('/assistant/firewall-rule-suggestion', { description })
      return data as AssistantResponse
    },
  })
}

export function useAuditLogs(params?: Record<string, unknown>) {
  return useQuery<AuditLog[]>({
    queryKey: queryKeys.auditLogs(params),
    queryFn: async () => {
      const { data } = await api.get('/audit/logs', { params })
      return data
    },
  })
}

// Metrics hooks
export function useMetricsLatest(instanceId: number, options?: Partial<UseQueryOptions<MetricSnapshot>>) {
  return useQuery<MetricSnapshot>({
    queryKey: queryKeys.metricsLatest(instanceId),
    queryFn: async () => {
      const { data } = await api.get(`/metrics/latest/${instanceId}`)
      return data
    },
    enabled: instanceId > 0,
    ...options,
  })
}

export function useMetricsQuery(params: MetricsQuery, options?: Partial<UseQueryOptions<MetricSnapshot[]>>) {
  return useQuery<MetricSnapshot[]>({
    queryKey: queryKeys.metricsQuery(params as Record<string, unknown>),
    queryFn: async () => {
      const { data } = await api.post('/metrics/query', params)
      return data
    },
    ...options,
  })
}

export function useMetricsSummary(params: MetricsQuery, options?: Partial<UseQueryOptions<MetricsSummary[]>>) {
  return useQuery<MetricsSummary[]>({
    queryKey: queryKeys.metricsSummary(params as Record<string, unknown>),
    queryFn: async () => {
      const { data } = await api.post('/metrics/summary', params)
      return data
    },
    ...options,
  })
}

export function useDashboardData(instanceId: number, options?: Partial<UseQueryOptions<DashboardData>>) {
  return useQuery<DashboardData>({
    queryKey: queryKeys.dashboardData(instanceId),
    queryFn: async () => {
      const { data } = await api.get(`/metrics/dashboard/${instanceId}`)
      return data
    },
    enabled: instanceId > 0,
    ...options,
  })
}

export interface MetricsOverview {
  instances: number
  active_instances: number
  firewall_rules: number
  mail_domains: number
  vpn_servers: number
}

export function useMetricsOverview(options?: Partial<UseQueryOptions<MetricsOverview>>) {
  return useQuery<MetricsOverview>({
    queryKey: queryKeys.metricsOverview,
    queryFn: async () => {
      const { data } = await api.get('/metrics/overview')
      return data
    },
    ...options,
  })
}

// Routing hooks
export function useRoutingRules(instanceId: number, options?: Partial<UseQueryOptions<RoutingRule[]>>) {
  return useQuery<RoutingRule[]>({
    queryKey: queryKeys.routingRules(instanceId),
    queryFn: async () => {
      const { data } = await api.get(`/routing/rules/${instanceId}`)
      return data
    },
    enabled: instanceId > 0,
    ...options,
  })
}

export function useCreateRoutingRule(instanceId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (rule: RoutingRuleCreate) => {
      const { data } = await api.post(`/routing/rules/${instanceId}`, rule)
      return data as RoutingRule
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.routingRules(instanceId) })
    },
  })
}

export function useUpdateRoutingRule(instanceId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, ...rule }: { id: number } & RoutingRuleUpdate) => {
      const { data } = await api.patch(`/routing/rules/${id}`, rule)
      return data as RoutingRule
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.routingRules(instanceId) })
    },
  })
}

export function useDeleteRoutingRule(instanceId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/routing/rules/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.routingRules(instanceId) })
    },
  })
}

export function useApplyRouting(instanceId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post(`/routing/apply/${instanceId}`)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.routingRules(instanceId) })
    },
  })
}

// LLM Config hooks
export function useLLMConfig(options?: Partial<UseQueryOptions<LLMConfig>>) {
  return useQuery<LLMConfig>({
    queryKey: ['llm-config'],
    queryFn: async () => {
      const { data } = await api.get('/assistant/config')
      return data
    },
    ...options,
  })
}

export function useUpdateLLMConfig() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (config: LLMConfig) => {
      const { data } = await api.post('/assistant/config', config)
      return data as LLMConfig
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['llm-config'] })
    },
  })
}

// LLM Admin hooks
export function useLLMProviders(options?: Partial<UseQueryOptions<LLMProvider[]>>) {
  return useQuery<LLMProvider[]>({
    queryKey: queryKeys.llmProviders,
    queryFn: async () => {
      const { data } = await api.get('/admin/llm/providers')
      return data
    },
    ...options,
  })
}

export function useCreateLLMProvider() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (provider: LLMProviderCreate) => {
      const { data } = await api.post('/admin/llm/providers', provider)
      return data as LLMProvider
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.llmProviders })
    },
  })
}

export function useUpdateLLMProvider() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, ...update }: { id: number } & LLMProviderUpdate) => {
      const { data } = await api.patch(`/admin/llm/providers/${id}`, update)
      return data as LLMProvider
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.llmProviders })
    },
  })
}

export function useDeleteLLMProvider() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/admin/llm/providers/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.llmProviders })
      queryClient.invalidateQueries({ queryKey: queryKeys.llmModels() })
    },
  })
}

export function useTestLLMProvider() {
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await api.post(`/admin/llm/providers/${id}/test`)
      return data as { status: string; response: string }
    },
  })
}

export function useLLMModels(providerId?: number, options?: Partial<UseQueryOptions<LLMModel[]>>) {
  return useQuery<LLMModel[]>({
    queryKey: queryKeys.llmModels(providerId),
    queryFn: async () => {
      const { data } = await api.get('/admin/llm/models', { params: providerId ? { provider_id: providerId } : undefined })
      return data
    },
    ...options,
  })
}

export function useCreateLLMModel() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (model: LLMModelCreate) => {
      const { data } = await api.post('/admin/llm/models', model)
      return data as LLMModel
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.llmModels() })
    },
  })
}

export function useUpdateLLMModel() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, ...update }: { id: number } & LLMModelUpdate) => {
      const { data } = await api.patch(`/admin/llm/models/${id}`, update)
      return data as LLMModel
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.llmModels() })
    },
  })
}

export function useDeleteLLMModel() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/admin/llm/models/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.llmModels() })
    },
  })
}

export function useLLMUseCaseConfigs(options?: Partial<UseQueryOptions<LLMUseCaseConfig[]>>) {
  return useQuery<LLMUseCaseConfig[]>({
    queryKey: queryKeys.llmUseCaseConfigs,
    queryFn: async () => {
      const { data } = await api.get('/admin/llm/use-cases')
      return data
    },
    ...options,
  })
}

export function useUpdateLLMUseCaseConfig() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, ...update }: { id: number } & LLMUseCaseConfigUpdate) => {
      const { data } = await api.patch(`/admin/llm/use-cases/${id}`, update)
      return data as LLMUseCaseConfig
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.llmUseCaseConfigs })
    },
  })
}

// LDAP Config hooks
export function useLDAPConfig(options?: Partial<UseQueryOptions<LDAPConfig | null>>) {
  return useQuery<LDAPConfig | null>({
    queryKey: ['ldap-config'],
    queryFn: async () => {
      const { data } = await api.get('/auth/ldap-config')
      return data as LDAPConfig | null
    },
    ...options,
  })
}

export function useUpdateLDAPConfig() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (config: LDAPConfig) => {
      const { data } = await api.post('/auth/ldap-config', config)
      return data as LDAPConfig
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ldap-config'] })
    },
  })
}

export function useDeleteLDAPConfig() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      await api.delete('/auth/ldap-config')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ldap-config'] })
    },
  })
}

export function useTestLDAPConnection() {
  return useMutation({
    mutationFn: async (config: LDAPConfig) => {
      const { data } = await api.post('/auth/test-ldap', config)
      return data as { status: string; message: string }
    },
  })
}
