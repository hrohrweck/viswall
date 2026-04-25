"""Initial migration with all models

Revision ID: e1580e735101
Revises: 
Create Date: 2026-04-25 01:57:06.639011

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e1580e735101'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create instances table
    op.create_table(
        'instances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('hostname', sa.String(length=255), nullable=False),
        sa.Column('api_endpoint', sa.String(length=500), nullable=False),
        sa.Column('api_key', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        sa.Column('capabilities', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('auth_backend', sa.String(length=20), nullable=True),
        sa.Column('role', sa.String(length=20), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('instances', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('preferences', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('instance_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.String(length=100), nullable=True),
        sa.Column('old_value', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('new_value', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['instance_id'], ['instances.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create firewall_rules table
    op.create_table(
        'firewall_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('instance_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.Column('source_type', sa.String(length=20), nullable=True),
        sa.Column('source_value', sa.String(length=255), nullable=True),
        sa.Column('dest_type', sa.String(length=20), nullable=True),
        sa.Column('dest_value', sa.String(length=255), nullable=True),
        sa.Column('service_protocol', sa.String(length=10), nullable=True),
        sa.Column('service_ports', sa.String(length=100), nullable=True),
        sa.Column('action', sa.String(length=10), nullable=True),
        sa.Column('log_enabled', sa.Boolean(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['instance_id'], ['instances.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create nat_rules table
    op.create_table(
        'nat_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('instance_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.Column('type', sa.String(length=20), nullable=True),
        sa.Column('interface', sa.String(length=50), nullable=True),
        sa.Column('source_network', sa.String(length=100), nullable=True),
        sa.Column('dest_network', sa.String(length=100), nullable=True),
        sa.Column('to_source', sa.String(length=100), nullable=True),
        sa.Column('to_destination', sa.String(length=100), nullable=True),
        sa.Column('service_protocol', sa.String(length=10), nullable=True),
        sa.Column('service_ports', sa.String(length=100), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['instance_id'], ['instances.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create network_interfaces table
    op.create_table(
        'network_interfaces',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('instance_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=True),
        sa.Column('config_type', sa.String(length=20), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('netmask', sa.String(length=45), nullable=True),
        sa.Column('gateway', sa.String(length=45), nullable=True),
        sa.Column('bandwidth_in', sa.Integer(), nullable=True),
        sa.Column('bandwidth_out', sa.Integer(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['instance_id'], ['instances.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create mail_domains table
    op.create_table(
        'mail_domains',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('instance_id', sa.Integer(), nullable=True),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.Column('spam_filter_enabled', sa.Boolean(), nullable=True),
        sa.Column('virus_scan_enabled', sa.Boolean(), nullable=True),
        sa.Column('dkim_enabled', sa.Boolean(), nullable=True),
        sa.Column('dmarc_enabled', sa.Boolean(), nullable=True),
        sa.Column('spf_enabled', sa.Boolean(), nullable=True),
        sa.Column('llm_enabled', sa.Boolean(), nullable=True),
        sa.Column('llm_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['instance_id'], ['instances.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create mail_users table
    op.create_table(
        'mail_users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('domain_id', sa.Integer(), nullable=True),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('quota_bytes', sa.Integer(), nullable=True),
        sa.Column('quota_used', sa.Integer(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.Column('forward_to', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('vacation_enabled', sa.Boolean(), nullable=True),
        sa.Column('vacation_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['domain_id'], ['mail_domains.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create metric_snapshots table
    op.create_table(
        'metric_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('instance_id', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('cpu_percent', sa.Float(), nullable=True),
        sa.Column('memory_percent', sa.Float(), nullable=True),
        sa.Column('memory_used_bytes', sa.Integer(), nullable=True),
        sa.Column('memory_total_bytes', sa.Integer(), nullable=True),
        sa.Column('disk_percent', sa.Float(), nullable=True),
        sa.Column('disk_used_bytes', sa.Integer(), nullable=True),
        sa.Column('disk_total_bytes', sa.Integer(), nullable=True),
        sa.Column('interface_stats', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('mail_queue_size', sa.Integer(), nullable=True),
        sa.Column('mail_inbound_count', sa.Integer(), nullable=True),
        sa.Column('mail_outbound_count', sa.Integer(), nullable=True),
        sa.Column('mail_spam_count', sa.Integer(), nullable=True),
        sa.Column('mail_virus_count', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create routing_rules table
    op.create_table(
        'routing_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('instance_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.Column('source_network', sa.String(length=50), nullable=True),
        sa.Column('dest_network', sa.String(length=50), nullable=True),
        sa.Column('service', sa.String(length=100), nullable=True),
        sa.Column('inbound_interface', sa.String(length=50), nullable=True),
        sa.Column('gateway', sa.String(length=45), nullable=True),
        sa.Column('outbound_interface', sa.String(length=50), nullable=True),
        sa.Column('mark', sa.Integer(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['instance_id'], ['instances.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create vpn_servers table
    op.create_table(
        'vpn_servers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('instance_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.Column('protocol', sa.String(length=20), nullable=False),
        sa.Column('listen_address', sa.String(length=45), nullable=True),
        sa.Column('listen_port', sa.Integer(), nullable=True),
        sa.Column('network_cidr', sa.String(length=50), nullable=True),
        sa.Column('dns_servers', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('push_routes', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('internet_redirect', sa.Boolean(), nullable=True),
        sa.Column('config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('cipher', sa.String(length=50), nullable=True),
        sa.Column('digest', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('connected_clients', sa.Integer(), nullable=True),
        sa.Column('bytes_received', sa.Integer(), nullable=True),
        sa.Column('bytes_sent', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['instance_id'], ['instances.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create vpn_clients table
    op.create_table(
        'vpn_clients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('server_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.Column('client_type', sa.String(length=20), nullable=True),
        sa.Column('auth_type', sa.String(length=20), nullable=True),
        sa.Column('public_key', sa.Text(), nullable=True),
        sa.Column('certificate', sa.Text(), nullable=True),
        sa.Column('private_key_ref', sa.String(length=255), nullable=True),
        sa.Column('psk', sa.String(length=512), nullable=True),
        sa.Column('assigned_ip', sa.String(length=45), nullable=True),
        sa.Column('allowed_ips', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('push_routes_override', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('last_connected', sa.DateTime(), nullable=True),
        sa.Column('last_ip', sa.String(length=45), nullable=True),
        sa.Column('connection_count', sa.Integer(), nullable=True),
        sa.Column('bytes_received', sa.Integer(), nullable=True),
        sa.Column('bytes_sent', sa.Integer(), nullable=True),
        sa.Column('config_qr', sa.Text(), nullable=True),
        sa.Column('config_file', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['server_id'], ['vpn_servers.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create vpn_connections table
    op.create_table(
        'vpn_connections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('server_id', sa.Integer(), nullable=True),
        sa.Column('client_id', sa.Integer(), nullable=True),
        sa.Column('protocol', sa.String(length=20), nullable=True),
        sa.Column('client_ip', sa.String(length=45), nullable=True),
        sa.Column('virtual_ip', sa.String(length=45), nullable=True),
        sa.Column('connected_at', sa.DateTime(), nullable=True),
        sa.Column('disconnected_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('bytes_received', sa.Integer(), nullable=True),
        sa.Column('bytes_sent', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('disconnect_reason', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['vpn_clients.id']),
        sa.ForeignKeyConstraint(['server_id'], ['vpn_servers.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create vpn_routes table
    op.create_table(
        'vpn_routes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('server_id', sa.Integer(), nullable=True),
        sa.Column('destination', sa.String(length=50), nullable=False),
        sa.Column('gateway', sa.String(length=45), nullable=True),
        sa.Column('metric', sa.Integer(), nullable=True),
        sa.Column('apply_to_all', sa.Boolean(), nullable=True),
        sa.Column('specific_clients', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['server_id'], ['vpn_servers.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create wireguard_peers table
    op.create_table(
        'wireguard_peers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('server_id', sa.Integer(), nullable=True),
        sa.Column('client_id', sa.Integer(), nullable=True),
        sa.Column('public_key', sa.String(length=255), nullable=False),
        sa.Column('preshared_key', sa.String(length=512), nullable=True),
        sa.Column('allowed_ips', sa.String(length=500), nullable=True),
        sa.Column('persistent_keepalive', sa.Integer(), nullable=True),
        sa.Column('bandwidth_limit_in', sa.Integer(), nullable=True),
        sa.Column('bandwidth_limit_out', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['vpn_clients.id']),
        sa.ForeignKeyConstraint(['server_id'], ['vpn_servers.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('public_key')
    )

    # Create ipsec_tunnels table
    op.create_table(
        'ipsec_tunnels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('server_id', sa.Integer(), nullable=True),
        sa.Column('client_id', sa.Integer(), nullable=True),
        sa.Column('tunnel_type', sa.String(length=20), nullable=True),
        sa.Column('ike_encryption', sa.String(length=50), nullable=True),
        sa.Column('ike_integrity', sa.String(length=50), nullable=True),
        sa.Column('ike_dh_group', sa.String(length=50), nullable=True),
        sa.Column('ike_lifetime', sa.Integer(), nullable=True),
        sa.Column('esp_encryption', sa.String(length=50), nullable=True),
        sa.Column('esp_integrity', sa.String(length=50), nullable=True),
        sa.Column('esp_dh_group', sa.String(length=50), nullable=True),
        sa.Column('esp_lifetime', sa.Integer(), nullable=True),
        sa.Column('auth_method', sa.String(length=20), nullable=True),
        sa.Column('local_id', sa.String(length=255), nullable=True),
        sa.Column('remote_id', sa.String(length=255), nullable=True),
        sa.Column('dpd_enabled', sa.Boolean(), nullable=True),
        sa.Column('dpd_interval', sa.Integer(), nullable=True),
        sa.Column('dpd_timeout', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['vpn_clients.id']),
        sa.ForeignKeyConstraint(['server_id'], ['vpn_servers.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create openvpn_configs table
    op.create_table(
        'openvpn_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('server_id', sa.Integer(), nullable=True),
        sa.Column('mode', sa.String(length=20), nullable=True),
        sa.Column('topology', sa.String(length=20), nullable=True),
        sa.Column('cipher', sa.String(length=50), nullable=True),
        sa.Column('auth_digest', sa.String(length=50), nullable=True),
        sa.Column('tls_version_min', sa.String(length=10), nullable=True),
        sa.Column('compression', sa.String(length=20), nullable=True),
        sa.Column('keepalive', sa.String(length=20), nullable=True),
        sa.Column('max_clients', sa.Integer(), nullable=True),
        sa.Column('ca_cert', sa.Text(), nullable=True),
        sa.Column('server_cert', sa.Text(), nullable=True),
        sa.Column('server_key', sa.Text(), nullable=True),
        sa.Column('crl', sa.Text(), nullable=True),
        sa.Column('duplicate_cn', sa.Boolean(), nullable=True),
        sa.Column('client_to_client', sa.Boolean(), nullable=True),
        sa.Column('plugins', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['server_id'], ['vpn_servers.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create qos_policies table
    op.create_table(
        'qos_policies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('instance_id', sa.Integer(), nullable=False),
        sa.Column('interface_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.Column('algorithm', sa.String(length=20), nullable=True),
        sa.Column('download_kbps', sa.Integer(), nullable=False),
        sa.Column('upload_kbps', sa.Integer(), nullable=False),
        sa.Column('interface_name', sa.String(length=50), nullable=False),
        sa.Column('applied', sa.Boolean(), nullable=True),
        sa.Column('last_applied_at', sa.DateTime(), nullable=True),
        sa.Column('apply_error', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['instance_id'], ['instances.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create qos_classes table
    op.create_table(
        'qos_classes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('policy_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('min_rate_kbps', sa.Integer(), nullable=False),
        sa.Column('max_rate_kbps', sa.Integer(), nullable=False),
        sa.Column('match_ports', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('match_dscp', sa.String(length=10), nullable=True),
        sa.Column('match_protocol', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['policy_id'], ['qos_policies.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('qos_classes')
    op.drop_table('qos_policies')
    op.drop_table('openvpn_configs')
    op.drop_table('ipsec_tunnels')
    op.drop_table('wireguard_peers')
    op.drop_table('vpn_routes')
    op.drop_table('vpn_connections')
    op.drop_table('vpn_clients')
    op.drop_table('vpn_servers')
    op.drop_table('routing_rules')
    op.drop_table('metric_snapshots')
    op.drop_table('mail_users')
    op.drop_table('mail_domains')
    op.drop_table('network_interfaces')
    op.drop_table('nat_rules')
    op.drop_table('firewall_rules')
    op.drop_table('audit_logs')
    op.drop_table('users')
    op.drop_table('instances')
