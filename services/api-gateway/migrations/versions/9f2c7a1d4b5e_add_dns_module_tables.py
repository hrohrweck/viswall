"""add_dns_module_tables

Revision ID: 9f2c7a1d4b5e
Revises: 6e439a8a2c2a
Create Date: 2026-04-26 11:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9f2c7a1d4b5e"
down_revision: Union[str, None] = "6e439a8a2c2a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dns_servers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("instance_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("listening_addresses", sa.JSON(), nullable=True),
        sa.Column("port", sa.Integer(), nullable=True),
        sa.Column("is_recursive", sa.Boolean(), nullable=True),
        sa.Column("is_authoritative", sa.Boolean(), nullable=True),
        sa.Column("forwarders", sa.JSON(), nullable=True),
        sa.Column("allow_query", sa.JSON(), nullable=True),
        sa.Column("allow_transfer", sa.JSON(), nullable=True),
        sa.Column("also_notify", sa.JSON(), nullable=True),
        sa.Column("dnssec_enabled", sa.Boolean(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["instance_id"], ["instances.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "dns_tsig_keys",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("server_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("algorithm", sa.String(length=50), nullable=True),
        sa.Column("secret", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("rotated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["server_id"], ["dns_servers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "dns_zones",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("server_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("zone_type", sa.String(length=20), nullable=False),
        sa.Column("is_reverse", sa.Boolean(), nullable=True),
        sa.Column("reverse_network", sa.String(length=50), nullable=True),
        sa.Column("serial", sa.Integer(), nullable=True),
        sa.Column("refresh", sa.Integer(), nullable=True),
        sa.Column("retry", sa.Integer(), nullable=True),
        sa.Column("expire", sa.Integer(), nullable=True),
        sa.Column("minimum_ttl", sa.Integer(), nullable=True),
        sa.Column("master_server_address", sa.String(length=255), nullable=True),
        sa.Column("forwarders", sa.JSON(), nullable=True),
        sa.Column("dnssec_enabled", sa.Boolean(), nullable=True),
        sa.Column("dnssec_algorithm", sa.String(length=20), nullable=True),
        sa.Column("dnssec_ksk_size", sa.Integer(), nullable=True),
        sa.Column("dnssec_zsk_size", sa.Integer(), nullable=True),
        sa.Column("dnssec_ds_record", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=True),
        sa.Column("transfer_tsig_key_id", sa.Integer(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["server_id"], ["dns_servers.id"]),
        sa.ForeignKeyConstraint(["transfer_tsig_key_id"], ["dns_tsig_keys.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "dns_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("zone_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("record_type", sa.String(length=10), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("ttl", sa.Integer(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=True),
        sa.Column("weight", sa.Integer(), nullable=True),
        sa.Column("port", sa.Integer(), nullable=True),
        sa.Column("flags", sa.String(length=10), nullable=True),
        sa.Column("tag", sa.String(length=50), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["zone_id"], ["dns_zones.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "dnssec_keys",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("zone_id", sa.Integer(), nullable=False),
        sa.Column("key_type", sa.String(length=10), nullable=False),
        sa.Column("algorithm", sa.String(length=30), nullable=False),
        sa.Column("key_size", sa.Integer(), nullable=False),
        sa.Column("key_tag", sa.Integer(), nullable=True),
        sa.Column("public_key_path", sa.String(length=500), nullable=True),
        sa.Column("private_key_path", sa.String(length=500), nullable=True),
        sa.Column("public_dnskey", sa.Text(), nullable=True),
        sa.Column("ds_record", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("activated_at", sa.DateTime(), nullable=True),
        sa.Column("rotated_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["zone_id"], ["dns_zones.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "dns_zone_slaves",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("zone_id", sa.Integer(), nullable=False),
        sa.Column("master_server_address", sa.String(length=255), nullable=False),
        sa.Column("tsig_key_id", sa.Integer(), nullable=True),
        sa.Column("last_transfer", sa.DateTime(), nullable=True),
        sa.Column("last_serial", sa.Integer(), nullable=True),
        sa.Column("transfer_status", sa.String(length=20), nullable=True),
        sa.Column("transfer_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["tsig_key_id"], ["dns_tsig_keys.id"]),
        sa.ForeignKeyConstraint(["zone_id"], ["dns_zones.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("dns_zone_slaves")
    op.drop_table("dnssec_keys")
    op.drop_table("dns_records")
    op.drop_table("dns_zones")
    op.drop_table("dns_tsig_keys")
    op.drop_table("dns_servers")
