"""firewall import fields: rule limit + interface ipv6/dns/routes

Revision ID: 866c6f4a7ebf
Revises: c9e4f7a21d58
Create Date: 2026-10-22 23:14:22.395420

Adds the firewall-import fields to the shared models:

  - firewall_rules.limit          (String, nullable) - rate limit, e.g.
                                   "10/minute burst 5 packets"
  - network_interfaces.ipv6_address (String, nullable)
  - network_interfaces.ipv6_gateway (String, nullable)
  - network_interfaces.dns_servers  (JSON, nullable) - nameserver strings
  - network_interfaces.routes       (JSON, nullable) - [{to, via, on_link}]

All columns are nullable; existing rows are untouched (no backfill, no
data loss). Hand-reviewed: autogenerate also proposed pre-existing
drift (llm_models provider FK, mail_aliases index, metric_snapshots FK,
qos_policies interface FK) which is out of scope for this migration and
was removed.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '866c6f4a7ebf'
down_revision: Union[str, None] = 'c9e4f7a21d58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('firewall_rules', sa.Column('limit', sa.String(length=255), nullable=True))
    op.add_column('network_interfaces', sa.Column('ipv6_address', sa.String(length=45), nullable=True))
    op.add_column('network_interfaces', sa.Column('ipv6_gateway', sa.String(length=45), nullable=True))
    op.add_column('network_interfaces', sa.Column('dns_servers', sa.JSON(), nullable=True))
    op.add_column('network_interfaces', sa.Column('routes', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('network_interfaces', 'routes')
    op.drop_column('network_interfaces', 'dns_servers')
    op.drop_column('network_interfaces', 'ipv6_gateway')
    op.drop_column('network_interfaces', 'ipv6_address')
    op.drop_column('firewall_rules', 'limit')
