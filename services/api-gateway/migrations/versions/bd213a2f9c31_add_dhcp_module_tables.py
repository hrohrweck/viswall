"""add_dhcp_module_tables

Revision ID: bd213a2f9c31
Revises: 9f2c7a1d4b5e
Create Date: 2026-04-26 16:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "bd213a2f9c31"
down_revision: Union[str, None] = "9f2c7a1d4b5e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dhcp_servers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("instance_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("kea_ctrl_agent_address", sa.String(length=255), nullable=True),
        sa.Column("kea_ctrl_agent_port", sa.Integer(), nullable=True),
        sa.Column("ha_enabled", sa.Boolean(), nullable=True),
        sa.Column("ha_mode", sa.String(length=20), nullable=True),
        sa.Column("ha_peer_address", sa.String(length=255), nullable=True),
        sa.Column("dhcpv4_enabled", sa.Boolean(), nullable=True),
        sa.Column("dhcpv6_enabled", sa.Boolean(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["instance_id"], ["instances.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "dhcp_subnets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("server_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("subnet", sa.String(length=100), nullable=False),
        sa.Column("type", sa.String(length=10), nullable=False),
        sa.Column("interface", sa.String(length=50), nullable=True),
        sa.Column("relay_addresses", sa.JSON(), nullable=True),
        sa.Column("domain_name", sa.String(length=255), nullable=True),
        sa.Column("dns_servers", sa.JSON(), nullable=True),
        sa.Column("ntp_servers", sa.JSON(), nullable=True),
        sa.Column("routers", sa.JSON(), nullable=True),
        sa.Column("lease_time_default", sa.Integer(), nullable=True),
        sa.Column("lease_time_max", sa.Integer(), nullable=True),
        sa.Column("lease_time_min", sa.Integer(), nullable=True),
        sa.Column("delegated_prefix_length", sa.Integer(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["server_id"], ["dhcp_servers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "dhcp_pools",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("subnet_id", sa.Integer(), nullable=False),
        sa.Column("start_address", sa.String(length=45), nullable=False),
        sa.Column("end_address", sa.String(length=45), nullable=False),
        sa.Column("type", sa.String(length=10), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["subnet_id"], ["dhcp_subnets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "dhcp_reservations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("subnet_id", sa.Integer(), nullable=False),
        sa.Column("hostname", sa.String(length=255), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=False),
        sa.Column("hw_address", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=10), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["subnet_id"], ["dhcp_subnets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "dhcp_options",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("subnet_id", sa.Integer(), nullable=False),
        sa.Column("option_code", sa.Integer(), nullable=False),
        sa.Column("option_name", sa.String(length=100), nullable=False),
        sa.Column("option_value", sa.Text(), nullable=False),
        sa.Column("type", sa.String(length=10), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["subnet_id"], ["dhcp_subnets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "dhcp_leases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("subnet_id", sa.Integer(), nullable=False),
        sa.Column("pool_id", sa.Integer(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=False),
        sa.Column("hw_address", sa.String(length=255), nullable=True),
        sa.Column("hostname", sa.String(length=255), nullable=True),
        sa.Column("client_id", sa.String(length=255), nullable=True),
        sa.Column("lease_start", sa.DateTime(), nullable=True),
        sa.Column("lease_end", sa.DateTime(), nullable=True),
        sa.Column("released_at", sa.DateTime(), nullable=True),
        sa.Column("state", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["pool_id"], ["dhcp_pools.id"]),
        sa.ForeignKeyConstraint(["subnet_id"], ["dhcp_subnets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("dhcp_leases")
    op.drop_table("dhcp_options")
    op.drop_table("dhcp_reservations")
    op.drop_table("dhcp_pools")
    op.drop_table("dhcp_subnets")
    op.drop_table("dhcp_servers")
