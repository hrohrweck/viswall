from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Enums
class AuthBackend(str, Enum):
    LOCAL = "local"
    LDAP = "ldap"
    ACTIVE_DIRECTORY = "ad"


class UserRole(str, Enum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"


class InstanceStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class FirewallAction(str, Enum):
    ACCEPT = "accept"
    DROP = "drop"
    REJECT = "reject"


# Instance Schemas
class InstanceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    hostname: str = Field(..., min_length=1, max_length=255)
    capabilities: List[str] = Field(default_factory=list)


class InstanceCreate(InstanceBase):
    api_key: Optional[str] = None  # Generated if not provided


class InstanceUpdate(BaseModel):
    name: Optional[str] = None
    hostname: Optional[str] = None
    status: Optional[InstanceStatus] = None
    capabilities: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None


class InstanceResponse(InstanceBase):
    id: int
    api_endpoint: str
    status: InstanceStatus
    last_seen: Optional[datetime]
    config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# User Schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: str = Field(..., max_length=255)
    auth_backend: AuthBackend = AuthBackend.LOCAL
    role: UserRole = UserRole.USER


class UserCreate(UserBase):
    password: Optional[str] = Field(None, min_length=8)
    instances: List[int] = Field(default_factory=list)


class UserUpdate(BaseModel):
    email: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    instances: Optional[List[int]] = None
    preferences: Optional[Dict[str, Any]] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    instances: List[int]
    preferences: Dict[str, Any]
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserPasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


# Auth Schemas
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class LDAPConfig(BaseModel):
    server_url: str
    bind_dn: str
    bind_password: str
    base_dn: str
    user_filter: str = "(objectClass=person)"
    group_filter: Optional[str] = None


# Firewall Rule Schemas
class FirewallRuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    enabled: bool = True
    source_type: str = "any"
    source_value: Optional[str] = None
    dest_type: str = "any"
    dest_value: Optional[str] = None
    service_protocol: str = "tcp"
    service_ports: Optional[str] = None
    action: FirewallAction = FirewallAction.ACCEPT
    log_enabled: bool = False


class FirewallRuleCreate(FirewallRuleBase):
    pass


class FirewallRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    source_type: Optional[str] = None
    source_value: Optional[str] = None
    dest_type: Optional[str] = None
    dest_value: Optional[str] = None
    service_protocol: Optional[str] = None
    service_ports: Optional[str] = None
    action: Optional[FirewallAction] = None
    log_enabled: Optional[bool] = None


class FirewallRuleResponse(FirewallRuleBase):
    id: int
    instance_id: int
    order_index: int
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime


# NAT Rule Schemas
class NATRuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    enabled: bool = True
    nat_type: str = "snat"  # snat, dnat, masquerade
    source_network: Optional[str] = None
    dest_network: Optional[str] = None
    service_protocol: str = "any"
    service_ports: Optional[str] = None
    inbound_interface: Optional[str] = None
    outbound_interface: Optional[str] = None
    translation_address: Optional[str] = None
    translation_ports: Optional[str] = None


class NATRuleCreate(NATRuleBase):
    pass


class NATRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    nat_type: Optional[str] = None
    source_network: Optional[str] = None
    dest_network: Optional[str] = None
    service_protocol: Optional[str] = None
    service_ports: Optional[str] = None
    inbound_interface: Optional[str] = None
    outbound_interface: Optional[str] = None
    translation_address: Optional[str] = None
    translation_ports: Optional[str] = None


class NATRuleResponse(NATRuleBase):
    id: int
    instance_id: int
    order_index: int
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# NAT Rule Schemas
class NATRuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    enabled: bool = True
    type: str = "snat"  # snat, dnat, masquerade
    interface: Optional[str] = None
    source_network: Optional[str] = None
    dest_network: Optional[str] = None
    to_source: Optional[str] = None
    to_destination: Optional[str] = None
    service_protocol: Optional[str] = None
    service_ports: Optional[str] = None

class NATRuleCreate(NATRuleBase):
    pass

class NATRuleResponse(NATRuleBase):
    id: int
    instance_id: int
    order_index: int
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NetworkInterfaceBase(BaseModel):
    name: str = Field(..., max_length=50)
    type: str = "other"
    config_type: str = "dhcp"
    ip_address: Optional[str] = None
    netmask: Optional[str] = None
    gateway: Optional[str] = None
    bandwidth_in: Optional[int] = None  # kbps
    bandwidth_out: Optional[int] = None
    enabled: bool = True


class NetworkInterfaceCreate(NetworkInterfaceBase):
    pass


class NetworkInterfaceResponse(NetworkInterfaceBase):
    id: int
    instance_id: int
    updated_at: datetime

    class Config:
        from_attributes = True


# Mail Domain Schemas
class MailDomainBase(BaseModel):
    domain: str = Field(..., max_length=255)
    enabled: bool = True
    spam_filter_enabled: bool = True
    virus_scan_enabled: bool = True
    dkim_enabled: bool = True
    dmarc_enabled: bool = True
    spf_enabled: bool = True
    llm_enabled: bool = False
    groupware_enabled: bool = False


class MailDomainCreate(MailDomainBase):
    llm_config: Optional[Dict[str, Any]] = None


class MailDomainUpdate(BaseModel):
    enabled: Optional[bool] = None
    spam_filter_enabled: Optional[bool] = None
    virus_scan_enabled: Optional[bool] = None
    dkim_enabled: Optional[bool] = None
    dmarc_enabled: Optional[bool] = None
    spf_enabled: Optional[bool] = None
    llm_enabled: Optional[bool] = None
    groupware_enabled: Optional[bool] = None
    llm_config: Optional[Dict[str, Any]] = None


class MailDomainResponse(MailDomainBase):
    id: int
    instance_id: int
    llm_config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Mail User Schemas
class MailUserBase(BaseModel):
    username: str = Field(..., max_length=100)
    full_name: Optional[str] = None
    quota_bytes: int = 1073741824
    enabled: bool = True


class MailUserCreate(MailUserBase):
    password: Optional[str] = None
    forward_to: List[str] = Field(default_factory=list)


class MailUserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None
    quota_bytes: Optional[int] = None
    enabled: Optional[bool] = None
    forward_to: Optional[List[str]] = None
    vacation_enabled: Optional[bool] = None
    vacation_message: Optional[str] = None


class MailUserResponse(MailUserBase):
    id: int
    domain_id: int
    quota_used: int
    forward_to: List[str]
    vacation_enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Category Config Schema
class CategoryConfig(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: str = Field(..., max_length=20)
    default_action: str = Field(default="deliver", max_length=20)


# Mail Message Schemas
class MailMessageBase(BaseModel):
    sender: str = Field(..., max_length=255)
    recipients: List[str] = Field(default_factory=list)
    subject: Optional[str] = Field(None, max_length=500)
    size_bytes: Optional[int] = None
    body_preview: Optional[str] = None


class MailMessageCreate(MailMessageBase):
    message_id: str = Field(..., max_length=255)
    domain_id: int


class MailMessageResponse(MailMessageBase):
    id: int
    domain_id: int
    message_id: str
    spam_score: Optional[float] = None
    virus_status: Optional[str] = None
    llm_category: Optional[str] = None
    llm_confidence: Optional[float] = None
    llm_reason: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    classified_at: Optional[datetime] = None
    action_taken: str = "pending"
    action_reason: Optional[str] = None
    action_taken_at: Optional[datetime] = None
    action_taken_by: Optional[int] = None
    status: str = "pending"
    received_at: datetime

    class Config:
        from_attributes = True


class MailClassificationResult(BaseModel):
    category: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str


class MailMessageListParams(BaseModel):
    category: Optional[str] = None
    status: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class MailMessageActionRequest(BaseModel):
    action: str = Field(..., max_length=20)
    reason: Optional[str] = None


# Metrics Schemas
class MetricSnapshotBase(BaseModel):
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    memory_used_bytes: Optional[int] = None
    memory_total_bytes: Optional[int] = None
    disk_percent: Optional[float] = None
    disk_used_bytes: Optional[int] = None
    disk_total_bytes: Optional[int] = None
    interface_stats: Optional[List[Dict[str, Any]]] = None
    mail_queue_size: Optional[int] = None
    mail_inbound_count: Optional[int] = None
    mail_outbound_count: Optional[int] = None
    mail_spam_count: Optional[int] = None
    mail_virus_count: Optional[int] = None


class MetricSnapshotCreate(MetricSnapshotBase):
    timestamp: Optional[datetime] = None


class MetricSnapshotResponse(MetricSnapshotBase):
    id: int
    instance_id: int
    timestamp: datetime

    class Config:
        from_attributes = True


class MetricsQuery(BaseModel):
    instance_ids: Optional[List[int]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    granularity: str = "5m"  # 1m, 5m, 1h, 1d


class MetricsSummary(BaseModel):
    instance_id: int
    cpu_avg: float
    cpu_max: float
    memory_avg: float
    memory_max: float
    disk_avg: float
    disk_max: float
    network_in_total: int
    network_out_total: int
    mail_total_inbound: int
    mail_total_outbound: int
    period_start: datetime
    period_end: datetime


# Routing Rule Schemas
class RoutingRuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    enabled: bool = True
    source_network: Optional[str] = None
    dest_network: Optional[str] = None
    service: Optional[str] = None
    inbound_interface: Optional[str] = None
    gateway: Optional[str] = None
    outbound_interface: Optional[str] = None
    mark: Optional[int] = None
    order_index: Optional[int] = None


class RoutingRuleCreate(RoutingRuleBase):
    pass


class RoutingRuleUpdate(BaseModel):
    name: Optional[str] = None
    enabled: Optional[bool] = None
    source_network: Optional[str] = None
    dest_network: Optional[str] = None
    service: Optional[str] = None
    inbound_interface: Optional[str] = None
    gateway: Optional[str] = None
    outbound_interface: Optional[str] = None
    mark: Optional[int] = None
    order_index: Optional[int] = None


class RoutingRuleResponse(RoutingRuleBase):
    id: int
    instance_id: int
    order_index: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Audit Log Schemas
class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    instance_id: Optional[int]
    action: str
    resource_type: str
    resource_id: Optional[str]
    old_value: Optional[Dict[str, Any]]
    new_value: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True


# LLM Configuration Schema
class LLMConfig(BaseModel):
    provider: str = "openai"  # openai, anthropic, local
    model: str = "gpt-4"
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    temperature: float = 0.3
    max_tokens: int = 500
    system_prompt: str = "You are an email classification assistant."

    # Classification settings
    auto_classify: bool = False
    confidence_threshold: float = 0.8
    categories: List[str] = Field(
        default_factory=lambda: [
            "important",
            "newsletter",
            "social",
            "promotional",
            "spam",
            "work",
        ]
    )


# ============================================================================
# VPN SCHEMAS - Multi-Protocol Support
# ============================================================================


class VPNProtocol(str, Enum):
    WIREGUARD = "wireguard"
    IPSEC = "ipsec"
    OPENVPN = "openvpn"
    PPTP = "pptp"
    L2TP = "l2tp"


class VPNStatus(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    RESTARTING = "restarting"


class VPNClientType(str, Enum):
    USER = "user"  # Road warrior
    SITE = "site"  # Site-to-site
    SERVICE = "service"  # Service account


class VPNAuthType(str, Enum):
    CERT = "cert"
    PASSWORD = "password"
    SSO = "sso"
    PSK = "psk"
    PUBLIC_KEY = "public_key"


# WireGuard Specific
class WireGuardConfig(BaseModel):
    private_key: Optional[str] = None
    public_key: Optional[str] = None
    listen_port: int = Field(default=51820, ge=1, le=65535)
    network_cidr: str = "10.200.0.0/24"
    post_up: Optional[str] = None
    post_down: Optional[str] = None

    # Performance tuning
    mtu: int = 1420


class WireGuardPeerConfig(BaseModel):
    public_key: str
    preshared_key: Optional[str] = None
    allowed_ips: str = "0.0.0.0/0, ::/0"
    persistent_keepalive: int = Field(default=25, ge=0, le=65535)
    endpoint: Optional[str] = None  # For site-to-site


# IPsec Specific
class IPSecConfig(BaseModel):
    tunnel_type: str = "ikev2"  # ikev2 (recommended), ikev1

    # Phase 1 (IKE) - Modern defaults
    ike_encryption: str = "aes256gcm16"
    ike_integrity: str = "sha384"
    ike_dh_group: str = "ecp384"  # Elliptic curve
    ike_lifetime: int = 86400

    # Phase 2 (ESP)
    esp_encryption: str = "aes256gcm16"
    esp_integrity: str = "sha384"
    esp_dh_group: Optional[str] = "ecp384"  # PFS
    esp_lifetime: int = 3600

    # Authentication
    auth_method: str = "pubkey"  # pubkey, psk, eap-mschapv2, eap-tls

    # Dead Peer Detection
    dpd_enabled: bool = True
    dpd_interval: int = 30
    dpd_timeout: int = 120

    # Mobile config
    mobike: bool = True  # IKEv2 Mobility and Multihoming


# OpenVPN Specific
class OpenVPNConfig(BaseModel):
    mode: str = "tun"  # tun (routed), tap (bridged)
    topology: str = "subnet"

    # Crypto - Modern secure defaults
    cipher: str = "AES-256-GCM"
    auth_digest: str = "SHA256"
    tls_version_min: str = "1.2"
    tls_cipher: str = (
        "TLS-ECDHE-ECDSA-WITH-AES-256-GCM-SHA384:TLS-ECDHE-RSA-WITH-AES-256-GCM-SHA384"
    )

    # Connection
    protocol: str = "udp"  # udp (recommended), tcp
    port: int = 1194

    # Performance
    compression: Optional[str] = None  # None recommended (VORACLE attack)
    fast_io: bool = True

    # Features
    duplicate_cn: bool = False
    client_to_client: bool = False
    max_clients: int = 1024

    # Keepalive
    keepalive_interval: int = 10
    keepalive_timeout: int = 120


# L2TP/IPsec Specific (Legacy)
class L2TPConfig(BaseModel):
    ppp_interface: str = "ppp0"
    ppp_options: List[str] = Field(
        default_factory=lambda: [
            "noaccomp",
            "nopcomp",
            "nocrtscts",
            "idle 1800",
            "mtu 1280",
            "mru 1280",
        ]
    )
    ipsec_psk: Optional[str] = None
    chap_secrets: bool = True
    ms_dns: List[str] = Field(default_factory=lambda: ["8.8.8.8", "8.8.4.4"])


# PPTP Specific (Legacy - not recommended)
class PPTPConfig(BaseModel):
    ppp_interface: str = "ppp0"
    require_mppe: bool = True  # MPPE encryption (still weak)
    ms_dns: List[str] = Field(default_factory=lambda: ["8.8.8.8"])


# Main VPN Server Schemas
class VPNServerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    enabled: bool = True
    protocol: VPNProtocol

    # Network
    listen_address: str = "0.0.0.0"
    listen_port: Optional[int] = None
    network_cidr: str = "10.200.0.0/24"

    # Client settings
    dns_servers: List[str] = Field(default_factory=lambda: ["1.1.1.1", "1.0.0.1"])
    push_routes: List[str] = Field(default_factory=list)
    internet_redirect: bool = False


class VPNServerCreate(VPNServerBase):
    # Protocol-specific configs
    wireguard_config: Optional[WireGuardConfig] = None
    ipsec_config: Optional[IPSecConfig] = None
    openvpn_config: Optional[OpenVPNConfig] = None
    l2tp_config: Optional[L2TPConfig] = None
    pptp_config: Optional[PPTPConfig] = None


class VPNServerUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    listen_address: Optional[str] = None
    listen_port: Optional[int] = None
    network_cidr: Optional[str] = None
    dns_servers: Optional[List[str]] = None
    push_routes: Optional[List[str]] = None
    internet_redirect: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


class VPNServerResponse(VPNServerBase):
    id: int
    instance_id: int
    status: VPNStatus
    config: Dict[str, Any]
    connected_clients: int
    bytes_received: int
    bytes_sent: int
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VPNServerStats(BaseModel):
    server_id: int
    status: VPNStatus
    uptime_seconds: int
    connected_clients: int
    total_bytes_received: int
    total_bytes_sent: int
    client_list: List[Dict[str, Any]]


# VPN Client Schemas
class VPNClientBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    enabled: bool = True
    client_type: VPNClientType = VPNClientType.USER
    auth_type: VPNAuthType = VPNAuthType.CERT

    # Network
    assigned_ip: Optional[str] = None
    allowed_ips: List[str] = Field(default_factory=list)

    # Access override
    push_routes_override: List[str] = Field(default_factory=list)


class VPNClientCreate(VPNClientBase):
    user_id: Optional[int] = None  # Associate with system user
    generate_qr: bool = True  # Generate QR code for mobile


class VPNClientUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    assigned_ip: Optional[str] = None
    allowed_ips: Optional[List[str]] = None
    push_routes_override: Optional[List[str]] = None


class VPNClientResponse(VPNClientBase):
    id: int
    server_id: int
    user_id: Optional[int]

    # Connection tracking
    last_connected: Optional[datetime]
    last_ip: Optional[str]
    connection_count: int
    bytes_received: int
    bytes_sent: int

    # For WireGuard
    public_key: Optional[str]

    # Config delivery
    config_qr: Optional[str]
    config_file: Optional[str]

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VPNClientConfig(BaseModel):
    """Client configuration file for download"""

    client_id: int
    server_name: str
    protocol: VPNProtocol
    config_format: str  # wg-quick, ovpn, mobileconfig, etc.
    config_data: str  # Base64 encoded
    filename: str


# VPN Connection Tracking
class VPNConnectionResponse(BaseModel):
    id: int
    server_id: int
    client_id: int
    client_name: str
    protocol: VPNProtocol
    client_ip: str
    virtual_ip: str
    connected_at: datetime
    bytes_received: int
    bytes_sent: int
    status: str

    class Config:
        from_attributes = True


# VPN Routing
class VPNRouteBase(BaseModel):
    destination: str = Field(
        ..., pattern=r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}$"
    )
    gateway: Optional[str] = None
    metric: int = 0
    apply_to_all: bool = True
    specific_clients: List[int] = Field(default_factory=list)
    description: Optional[str] = None


class VPNRouteCreate(VPNRouteBase):
    pass


class VPNRouteResponse(VPNRouteBase):
    id: int
    server_id: int
    order_index: int
    created_at: datetime

    class Config:
        from_attributes = True


# Bulk operations
class VPNBulkGenerateRequest(BaseModel):
    server_id: int
    count: int = Field(..., ge=1, le=100)
    name_prefix: str = "client"
    auth_type: VPNAuthType = VPNAuthType.PUBLIC_KEY
    generate_qr: bool = True


class VPNBulkGenerateResponse(BaseModel):
    generated: int
    clients: List[VPNClientResponse]
    configs_zip: str  # Base64 encoded zip file


# Recommended protocols helper
class VPNProtocolRecommendation(BaseModel):
    protocol: VPNProtocol
    priority: int  # 1 = highest recommendation
    security_score: int  # 0-100
    performance_score: int  # 0-100
    compatibility_score: int  # 0-100
    description: str
    use_cases: List[str]


# ============================================================================
# TRAFFIC SHAPING / QoS SCHEMAS
# ============================================================================


class QoSAlgorithm(str, Enum):
    CAKE = "cake"
    FQ_CODEL = "fq_codel"
    HTB = "htb"


# --- QoS Traffic Class (used inside HTB policies) ---


class QoSClassBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    priority: int = Field(default=2, ge=1, le=3)
    min_rate_kbps: int = Field(..., gt=0, description="Guaranteed bandwidth in kbps")
    max_rate_kbps: int = Field(..., gt=0, description="Burst ceiling in kbps")
    match_ports: List[int] = Field(
        default_factory=list, description="Destination port numbers to match"
    )
    match_dscp: Optional[str] = Field(
        default=None, max_length=10, description="DSCP code point (e.g. EF, AF41)"
    )
    match_protocol: str = Field(default="any", description="tcp | udp | any")


class QoSClassCreate(QoSClassBase):
    pass


class QoSClassUpdate(BaseModel):
    name: Optional[str] = None
    priority: Optional[int] = Field(default=None, ge=1, le=3)
    min_rate_kbps: Optional[int] = Field(default=None, gt=0)
    max_rate_kbps: Optional[int] = Field(default=None, gt=0)
    match_ports: Optional[List[int]] = None
    match_dscp: Optional[str] = None
    match_protocol: Optional[str] = None


class QoSClassResponse(QoSClassBase):
    id: int
    policy_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- QoS Policy ---


class QoSPolicyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    enabled: bool = True
    interface_name: str = Field(
        ..., min_length=1, max_length=50, description="Linux interface name, e.g. eth0"
    )
    interface_id: Optional[int] = Field(
        default=None, description="FK to network_interfaces (optional)"
    )
    algorithm: QoSAlgorithm = QoSAlgorithm.CAKE
    download_kbps: int = Field(..., gt=0, description="Ingress rate ceiling in kbps")
    upload_kbps: int = Field(..., gt=0, description="Egress rate ceiling in kbps")


class QoSPolicyCreate(QoSPolicyBase):
    # For HTB, caller may supply custom classes; otherwise defaults are created
    classes: List[QoSClassCreate] = Field(
        default_factory=list,
        description="Traffic classes (HTB only). Leave empty for auto-defaults.",
    )


class QoSPolicyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    algorithm: Optional[QoSAlgorithm] = None
    download_kbps: Optional[int] = Field(default=None, gt=0)
    upload_kbps: Optional[int] = Field(default=None, gt=0)


class QoSPolicyResponse(QoSPolicyBase):
    id: int
    instance_id: int
    applied: bool
    last_applied_at: Optional[datetime]
    apply_error: Optional[str]
    classes: List[QoSClassResponse] = Field(default_factory=list)
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Live statistics returned by the firewall agent ---


class QoSQueueStats(BaseModel):
    """Per-qdisc/queue statistics parsed from tc -s output"""

    qdisc: str
    sent_bytes: int = 0
    sent_pkts: int = 0
    dropped_pkts: int = 0
    overlimits: int = 0
    backlog_bytes: int = 0
    backlog_pkts: int = 0


class QoSStatsResponse(BaseModel):
    policy_id: int
    interface: str
    algorithm: str
    download_kbps: int
    upload_kbps: int
    queues: List[QoSQueueStats] = Field(default_factory=list)
    raw: Optional[Dict[str, Any]] = None  # full tc -s json for advanced display
    collected_at: datetime


# --- Agent payload (sent from API gateway → firewall agent) ---


class QoSApplyRequest(BaseModel):
    """Payload the API gateway POSTs to the firewall agent."""

    policy_id: int
    interface: str
    algorithm: QoSAlgorithm
    download_kbps: int
    upload_kbps: int
    classes: List[QoSClassCreate] = Field(default_factory=list)


class QoSApplyResponse(BaseModel):
    success: bool
    message: str
    applied_at: Optional[datetime] = None
