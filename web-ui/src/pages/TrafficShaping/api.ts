import { api } from '../../utils/api'

export interface Instance {
  id: number
  name: string
  hostname: string
  status: string
}

export interface QoSClass {
  id: number
  policy_id: number
  name: string
  priority: number
  min_rate_kbps: number
  max_rate_kbps: number
  match_ports: number[]
  match_dscp: string | null
  match_protocol: string
  created_at: string
  updated_at: string
}

export interface QoSPolicy {
  id: number
  instance_id: number
  name: string
  description: string | null
  enabled: boolean
  interface_name: string
  interface_id: number | null
  algorithm: 'cake' | 'fq_codel' | 'htb'
  download_kbps: number
  upload_kbps: number
  applied: boolean
  last_applied_at: string | null
  apply_error: string | null
  classes: QoSClass[]
  created_by: number | null
  created_at: string
  updated_at: string
}

export interface QoSQueueStats {
  qdisc: string
  sent_bytes: number
  sent_pkts: number
  dropped_pkts: number
  overlimits: number
  backlog_bytes: number
  backlog_pkts: number
}

export interface QoSStats {
  policy_id: number
  interface: string
  algorithm: string
  download_kbps: number
  upload_kbps: number
  queues: QoSQueueStats[]
  raw: Record<string, any> | null
  collected_at: string
}

export interface QoSPolicyCreate {
  name: string
  description?: string
  enabled?: boolean
  interface_name: string
  interface_id?: number | null
  algorithm: 'cake' | 'fq_codel' | 'htb'
  download_kbps: number
  upload_kbps: number
  classes?: {
    name: string
    priority: number
    min_rate_kbps: number
    max_rate_kbps: number
    match_ports?: number[]
    match_dscp?: string | null
    match_protocol?: string
  }[]
}

export interface QoSPolicyUpdate {
  name?: string
  description?: string
  enabled?: boolean
  algorithm?: 'cake' | 'fq_codel' | 'htb'
  download_kbps?: number
  upload_kbps?: number
}

export const qosApi = {
  list: async (instanceId: number): Promise<QoSPolicy[]> => {
    const res = await api.get<QoSPolicy[]>(`/firewall/qos/${instanceId}`)
    return res.data
  },

  get: async (instanceId: number, policyId: number): Promise<QoSPolicy> => {
    const res = await api.get<QoSPolicy>(`/firewall/qos/${instanceId}/${policyId}`)
    return res.data
  },

  create: async (instanceId: number, data: QoSPolicyCreate): Promise<QoSPolicy> => {
    const res = await api.post<QoSPolicy>(`/firewall/qos/${instanceId}`, data)
    return res.data
  },

  update: async (
    instanceId: number,
    policyId: number,
    data: QoSPolicyUpdate
  ): Promise<QoSPolicy> => {
    const res = await api.patch<QoSPolicy>(`/firewall/qos/${instanceId}/${policyId}`, data)
    return res.data
  },

  delete: async (instanceId: number, policyId: number): Promise<void> => {
    await api.delete(`/firewall/qos/${instanceId}/${policyId}`)
  },

  apply: async (instanceId: number, policyId: number): Promise<{ status: string }> => {
    const res = await api.post<{ status: string }>(
      `/firewall/qos/${instanceId}/${policyId}/apply`
    )
    return res.data
  },

  stats: async (instanceId: number, policyId: number): Promise<QoSStats> => {
    const res = await api.get<QoSStats>(`/firewall/qos/${instanceId}/${policyId}/stats`)
    return res.data
  },

  createClass: async (
    instanceId: number,
    policyId: number,
    data: Partial<QoSClass>
  ): Promise<QoSClass> => {
    const res = await api.post<QoSClass>(
      `/firewall/qos/${instanceId}/${policyId}/classes`,
      data
    )
    return res.data
  },

  deleteClass: async (instanceId: number, policyId: number, classId: number): Promise<void> => {
    await api.delete(`/firewall/qos/${instanceId}/${policyId}/classes/${classId}`)
  },
}
