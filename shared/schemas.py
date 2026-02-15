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
    
    class Config:
        from_attributes = True

# Network Interface Schemas
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
    categories: List[str] = Field(default_factory=lambda: [
        "important", "newsletter", "social", "promotional", "spam", "work"
    ])
