"""Widen VPN byte counters to BigInteger.

The bytes_received/bytes_sent columns on vpn_servers, vpn_clients and
vpn_connections were INTEGER (int32, max ~2.1 GB). Cumulative per-client
transfer counters overflow int32 on busy tunnels, so the counters wrap and
traffic accounting goes negative. Widen them to BIGINT, matching the
metric_snapshots and mail quota byte columns.

Revision ID: e5a9c3d7f1b2
Revises: d116b942b744
Create Date: 2026-11-20
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e5a9c3d7f1b2"
down_revision = "d116b942b744"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "vpn_servers",
        "bytes_received",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        nullable=True,
    )
    op.alter_column(
        "vpn_servers",
        "bytes_sent",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        nullable=True,
    )
    op.alter_column(
        "vpn_clients",
        "bytes_received",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        nullable=True,
    )
    op.alter_column(
        "vpn_clients",
        "bytes_sent",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        nullable=True,
    )
    op.alter_column(
        "vpn_connections",
        "bytes_received",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        nullable=True,
    )
    op.alter_column(
        "vpn_connections",
        "bytes_sent",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "vpn_connections",
        "bytes_sent",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        nullable=True,
    )
    op.alter_column(
        "vpn_connections",
        "bytes_received",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        nullable=True,
    )
    op.alter_column(
        "vpn_clients",
        "bytes_sent",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        nullable=True,
    )
    op.alter_column(
        "vpn_clients",
        "bytes_received",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        nullable=True,
    )
    op.alter_column(
        "vpn_servers",
        "bytes_sent",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        nullable=True,
    )
    op.alter_column(
        "vpn_servers",
        "bytes_received",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        nullable=True,
    )
