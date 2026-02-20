from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Text,
    Float,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Instance(Base):
    """Managed viswall instances"""

    __tablename__ = "instances"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    hostname = Column(String(255), nullable=False)
    api_endpoint = Column(String(500), nullable=False)
    api_key = Column(String(255), nullable=False)
    status = Column(String(20), default="active")  # active, inactive, error
    last_seen = Column(DateTime, default=datetime.utcnow)
    capabilities = Column(JSON, default=list)  # ["mail", "firewall", "vpn"]
    config = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base):
    """User accounts with role-based access"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=True)  # null for LDAP/AD users
    auth_backend = Column(String(20), default="local")  # local, ldap, ad
    role = Column(String(20), default="user")  # superadmin, admin, user, readonly
    is_active = Column(Boolean, default=True)
    instances = Column(JSON, default=list)  # Instance IDs user can access
    preferences = Column(JSON, default=dict)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    """Audit trail for all changes"""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    instance_id = Column(Integer, ForeignKey("instances.id"))
    action = Column(String(50), nullable=False)  # create, update, delete, login
    resource_type = Column(String(50), nullable=False)  # firewall_rule, user, etc.
    resource_id = Column(String(100))
    old_value = Column(JSON)
    new_value = Column(JSON)
    ip_address = Column(String(45))
    timestamp = Column(DateTime, default=datetime.utcnow)


class FirewallRule(Base):
    """Firewall rules stored centrally"""

    __tablename__ = "firewall_rules"

    id = Column(Integer, primary_key=True)
    instance_id = Column(Integer, ForeignKey("instances.id"))
    name = Column(String(100), nullable=False)
    description = Column(Text)
    enabled = Column(Boolean, default=True)

    # Rule definition
    source_type = Column(String(20))  # any, host, network, range
    source_value = Column(String(255))
    dest_type = Column(String(20))
    dest_value = Column(String(255))
    service_protocol = Column(String(10))  # tcp, udp, icmp, any
    service_ports = Column(String(100))

    action = Column(String(10), default="accept")  # accept, drop, reject
    log_enabled = Column(Boolean, default=False)
    order_index = Column(Integer, default=0)

    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class NATRule(Base):
    """NAT rules for source/destination NAT"""
    __tablename__ = "nat_rules"

    id = Column(Integer, primary_key=True)
    instance_id = Column(Integer, ForeignKey("instances.id"))
    name = Column(String(100), nullable=False)
    description = Column(Text)
    enabled = Column(Boolean, default=True)

    type = Column(String(20), default="snat")  # snat, dnat, masquerade
    interface = Column(String(50))
    source_network = Column(String(100))
    dest_network = Column(String(100))
    to_source = Column(String(100))
    to_destination = Column(String(100))
    service_protocol = Column(String(10))
    service_ports = Column(String(100))

    order_index = Column(Integer, default=0)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NetworkInterface(Base):
    """Network interface configuration"""

    __tablename__ = "network_interfaces"

    id = Column(Integer, primary_key=True)
    instance_id = Column(Integer, ForeignKey("instances.id"))
    name = Column(String(50), nullable=False)  # eth0, eth1, etc.
    type = Column(String(20))  # wan, lan, dmz, other

    # IP Configuration
    config_type = Column(String(20), default="dhcp")  # dhcp, static
    ip_address = Column(String(45))
    netmask = Column(String(45))
    gateway = Column(String(45))

    # Traffic shaping
    bandwidth_in = Column(Integer)  # kbps
    bandwidth_out = Column(Integer)

    enabled = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MailDomain(Base):
    """Email domains managed by the system"""

    __tablename__ = "mail_domains"

    id = Column(Integer, primary_key=True)
    instance_id = Column(Integer, ForeignKey("instances.id"))
    domain = Column(String(255), nullable=False)
    enabled = Column(Boolean, default=True)

    # Security settings
    spam_filter_enabled = Column(Boolean, default=True)
    virus_scan_enabled = Column(Boolean, default=True)
    dkim_enabled = Column(Boolean, default=True)
    dmarc_enabled = Column(Boolean, default=True)
    spf_enabled = Column(Boolean, default=True)

    # LLM classification
    llm_enabled = Column(Boolean, default=False)
    llm_config = Column(JSON, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MailUser(Base):
    """Email users"""

    __tablename__ = "mail_users"

    id = Column(Integer, primary_key=True)
    domain_id = Column(Integer, ForeignKey("mail_domains.id"))
    username = Column(String(100), nullable=False)
    password_hash = Column(String(255))
    full_name = Column(String(255))
    quota_bytes = Column(Integer, default=1073741824)  # 1GB default
    quota_used = Column(Integer, default=0)
    enabled = Column(Boolean, default=True)

    # Delivery options
    forward_to = Column(JSON, default=list)
    vacation_enabled = Column(Boolean, default=False)
    vacation_message = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MetricSnapshot(Base):
    """Time-series metrics from instances"""

    __tablename__ = "metric_snapshots"

    id = Column(Integer, primary_key=True)
    instance_id = Column(Integer, ForeignKey("instances.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)

    # System metrics
    cpu_percent = Column(Float)
    memory_percent = Column(Float)
    memory_used_bytes = Column(Integer)
    memory_total_bytes = Column(Integer)
    disk_percent = Column(Float)
    disk_used_bytes = Column(Integer)
    disk_total_bytes = Column(Integer)

    # Network metrics (stored as JSON for flexibility)
    interface_stats = Column(
        JSON
    )  # [{"name": "eth0", "rx_bytes": ..., "tx_bytes": ...}]

    # Mail metrics
    mail_queue_size = Column(Integer)
    mail_inbound_count = Column(Integer)
    mail_outbound_count = Column(Integer)
    mail_spam_count = Column(Integer)
    mail_virus_count = Column(Integer)


class RoutingRule(Base):
    """Policy-based routing rules"""

    __tablename__ = "routing_rules"

    id = Column(Integer, primary_key=True)
    instance_id = Column(Integer, ForeignKey("instances.id"))
    name = Column(String(100), nullable=False)
    enabled = Column(Boolean, default=True)

    # Match conditions
    source_network = Column(String(50))
    dest_network = Column(String(50))
    service = Column(String(100))
    inbound_interface = Column(String(50))

    # Action
    gateway = Column(String(45))
    outbound_interface = Column(String(50))
    mark = Column(Integer)  # fwmark for traffic shaping

    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NATRule(Base):
    """NAT rules for source/destination NAT"""

    __tablename__ = "nat_rules"

    id = Column(Integer, primary_key=True)
    instance_id = Column(Integer, ForeignKey("instances.id"))
    name = Column(String(100), nullable=False)
    description = Column(Text)
    enabled = Column(Boolean, default=True)

    # NAT type: snat, dnat, masquerade
    nat_type = Column(String(20), default="snat")

    # Match conditions
    source_network = Column(String(50))
    dest_network = Column(String(50))
    service_protocol = Column(String(10))
    service_ports = Column(String(100))
    inbound_interface = Column(String(50))
    outbound_interface = Column(String(50))

    # NAT action
    translation_address = Column(String(45))
    translation_ports = Column(String(100))

    order_index = Column(Integer, default=0)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# VPN MODELS - Modern and Legacy Protocol Support
# ============================================================================


class VPNServer(Base):
    """VPN server configurations - multi-protocol support"""

    __tablename__ = "vpn_servers"

    id = Column(Integer, primary_key=True)
    instance_id = Column(Integer, ForeignKey("instances.id"))

    # Basic info
    name = Column(String(100), nullable=False)
    description = Column(Text)
    enabled = Column(Boolean, default=True)

    # Protocol: wireguard, ipsec, openvpn, pptp, l2tp
    protocol = Column(String(20), nullable=False)

    # Network configuration
    listen_address = Column(String(45), default="0.0.0.0")
    listen_port = Column(Integer)
    network_cidr = Column(String(50))  # VPN subnet (e.g., 10.200.0.0/24)

    # DNS and routing
    dns_servers = Column(JSON, default=list)
    push_routes = Column(JSON, default=list)  # Routes to push to clients
    internet_redirect = Column(
        Boolean, default=False
    )  # Redirect all traffic through VPN

    # Protocol-specific configuration stored as JSON
    config = Column(JSON, default=dict)

    # Crypto settings (protocol-specific)
    cipher = Column(String(50))
    digest = Column(String(50))

    # Status
    status = Column(String(20), default="stopped")  # running, stopped, error
    connected_clients = Column(Integer, default=0)
    bytes_received = Column(Integer, default=0)
    bytes_sent = Column(Integer, default=0)

    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VPNClient(Base):
    """VPN client configurations (for site-to-site or user clients)"""

    __tablename__ = "vpn_clients"

    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey("vpn_servers.id"))

    # Client identification
    name = Column(String(100), nullable=False)
    description = Column(Text)
    enabled = Column(Boolean, default=True)

    # Client type: user (road warrior), site (site-to-site), service
    client_type = Column(String(20), default="user")

    # Authentication
    auth_type = Column(String(20), default="cert")  # cert, password, sso, psk

    # Credentials (encrypted or references)
    public_key = Column(Text)  # For WireGuard
    certificate = Column(Text)  # For OpenVPN/IPsec
    private_key_ref = Column(String(255))  # Reference to secure storage
    psk = Column(String(512))  # Pre-shared key for IPsec/L2TP

    # Client addressing
    assigned_ip = Column(String(45))  # Static assignment (optional)

    # Access control
    allowed_ips = Column(JSON, default=list)  # Allowed source IPs
    push_routes_override = Column(JSON, default=list)

    # User association (for user-type clients)
    user_id = Column(Integer, ForeignKey("users.id"))

    # Connection tracking
    last_connected = Column(DateTime)
    last_ip = Column(String(45))
    connection_count = Column(Integer, default=0)
    bytes_received = Column(Integer, default=0)
    bytes_sent = Column(Integer, default=0)

    # QR code / config file for mobile clients
    config_qr = Column(Text)
    config_file = Column(Text)  # Base64 encoded config

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VPNConnection(Base):
    """Active and historical VPN connections"""

    __tablename__ = "vpn_connections"

    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey("vpn_servers.id"))
    client_id = Column(Integer, ForeignKey("vpn_clients.id"))

    # Connection details
    protocol = Column(String(20))
    client_ip = Column(String(45))  # Real client IP
    virtual_ip = Column(String(45))  # Assigned VPN IP

    # Timestamps
    connected_at = Column(DateTime, default=datetime.utcnow)
    disconnected_at = Column(DateTime)
    duration_seconds = Column(Integer)

    # Data transfer
    bytes_received = Column(Integer, default=0)
    bytes_sent = Column(Integer, default=0)

    # Status
    status = Column(String(20), default="active")  # active, disconnected, error
    disconnect_reason = Column(String(100))


class WireGuardPeer(Base):
    """WireGuard-specific peer configuration (optimized table)"""

    __tablename__ = "wireguard_peers"

    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey("vpn_servers.id"))
    client_id = Column(Integer, ForeignKey("vpn_clients.id"))

    # WireGuard specific
    public_key = Column(String(255), nullable=False, unique=True)
    preshared_key = Column(String(512))

    # AllowedIPs in WireGuard format
    allowed_ips = Column(String(500), default="0.0.0.0/0, ::/0")

    # Persistent keepalive (seconds)
    persistent_keepalive = Column(Integer, default=25)

    # QoS
    bandwidth_limit_in = Column(Integer)  # kbps
    bandwidth_limit_out = Column(Integer)


class IPSecTunnel(Base):
    """IPsec tunnel configurations (IKEv2, IKEv1)"""

    __tablename__ = "ipsec_tunnels"

    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey("vpn_servers.id"))
    client_id = Column(Integer, ForeignKey("vpn_clients.id"))

    # IPsec specifics
    tunnel_type = Column(String(20), default="ikev2")  # ikev2, ikev1

    # Phase 1 (IKE)
    ike_encryption = Column(String(50), default="aes256")
    ike_integrity = Column(String(50), default="sha256")
    ike_dh_group = Column(String(50), default="modp2048")
    ike_lifetime = Column(Integer, default=86400)

    # Phase 2 (ESP)
    esp_encryption = Column(String(50), default="aes256")
    esp_integrity = Column(String(50), default="sha256")
    esp_dh_group = Column(String(50))  # For PFS
    esp_lifetime = Column(Integer, default=3600)

    # Authentication
    auth_method = Column(String(20), default="cert")  # cert, psk, eap
    local_id = Column(String(255))
    remote_id = Column(String(255))

    # Dead Peer Detection
    dpd_enabled = Column(Boolean, default=True)
    dpd_interval = Column(Integer, default=30)
    dpd_timeout = Column(Integer, default=120)


class OpenVPNConfig(Base):
    """OpenVPN-specific configurations"""

    __tablename__ = "openvpn_configs"

    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey("vpn_servers.id"))

    # Protocol mode
    mode = Column(String(20), default="tun")  # tun (layer 3), tap (layer 2)
    topology = Column(String(20), default="subnet")  # subnet, net30, p2p

    # Crypto
    cipher = Column(String(50), default="AES-256-GCM")
    auth_digest = Column(String(50), default="SHA256")
    tls_version_min = Column(String(10), default="1.2")

    # Compression
    compression = Column(String(20))  # lz4, lzo, stub-v2

    # Connection settings
    keepalive = Column(String(20), default="10 120")  # ping/ping-restart
    max_clients = Column(Integer, default=1024)

    # Certificate settings
    ca_cert = Column(Text)
    server_cert = Column(Text)
    server_key = Column(Text)
    crl = Column(Text)  # Certificate Revocation List

    # Advanced options
    duplicate_cn = Column(Boolean, default=False)  # Allow multiple connections per cert
    client_to_client = Column(Boolean, default=False)

    # Plugin configs (auth, etc.)
    plugins = Column(JSON, default=list)


class VPNRoute(Base):
    """VPN-specific routing rules (split tunneling, etc.)"""

    __tablename__ = "vpn_routes"

    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey("vpn_servers.id"))

    # Route definition
    destination = Column(String(50), nullable=False)  # CIDR
    gateway = Column(String(45))
    metric = Column(Integer, default=0)

    # Scope
    apply_to_all = Column(Boolean, default=True)
    specific_clients = Column(JSON, default=list)  # Client IDs if not all

    # Description
    description = Column(String(255))

    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# TRAFFIC SHAPING / QoS MODELS
# ============================================================================


class QoSPolicy(Base):
    """QoS policy attached to a network interface on an instance.

    One policy per interface; algorithm determines how tc is configured:
      - cake     : single-qdisc, best for home/SMB (default)
      - fq_codel : fair-queueing CoDel, lower overhead
      - htb      : hierarchical token bucket, supports per-class priorities
    """

    __tablename__ = "qos_policies"

    id = Column(Integer, primary_key=True)
    instance_id = Column(Integer, ForeignKey("instances.id"), nullable=False)
    interface_id = Column(Integer, ForeignKey("network_interfaces.id"), nullable=True)

    # Human-readable label (auto-filled from interface name if blank)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    enabled = Column(Boolean, default=True)

    # tc algorithm
    algorithm = Column(String(20), default="cake")  # cake | fq_codel | htb

    # Bandwidth limits (kbps); 0 = unlimited
    download_kbps = Column(Integer, nullable=False)
    upload_kbps = Column(Integer, nullable=False)

    # Cached interface name so the policy stays useful even if
    # NetworkInterface row is deleted
    interface_name = Column(String(50), nullable=False)

    # Deployment state written back by the agent
    applied = Column(Boolean, default=False)
    last_applied_at = Column(DateTime)
    apply_error = Column(Text)

    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    classes = relationship(
        "QoSClass",
        back_populates="policy",
        cascade="all, delete-orphan",
        order_by="QoSClass.priority",
    )


class QoSClass(Base):
    """Traffic class within an HTB QoS policy.

    Only used when QoSPolicy.algorithm == 'htb'.  Pre-populated with
    three sensible defaults (VoIP/SSH, General, Bulk) when a policy is
    created; the administrator can customise or delete them.
    """

    __tablename__ = "qos_classes"

    id = Column(Integer, primary_key=True)
    policy_id = Column(Integer, ForeignKey("qos_policies.id"), nullable=False)

    name = Column(String(50), nullable=False)  # e.g. "VoIP", "General", "Bulk"
    priority = Column(Integer, default=2)  # 1 = highest, 3 = lowest

    # Bandwidth allocation (kbps); ceil defaults to policy ceiling
    min_rate_kbps = Column(Integer, nullable=False)
    max_rate_kbps = Column(Integer, nullable=False)

    # Traffic matching (any field may be NULL = match-all)
    match_ports = Column(JSON, default=list)  # list[int]
    match_dscp = Column(String(10))  # e.g. "EF", "AF41"
    match_protocol = Column(String(10), default="any")  # tcp | udp | any

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship back to policy
    policy = relationship("QoSPolicy", back_populates="classes")
