from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Text, Float
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
    interface_stats = Column(JSON)  # [{"name": "eth0", "rx_bytes": ..., "tx_bytes": ...}]
    
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
