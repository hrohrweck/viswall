"""add_vpn_ipv6_tunnel_network

Revision ID: 6e439a8a2c2a
Revises: d4a8f2e1b3c0
Create Date: 2026-04-25 20:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '6e439a8a2c2a'
down_revision: Union[str, None] = 'd4a8f2e1b3c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('vpn_servers', sa.Column('ipv6_tunnel_network', sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column('vpn_servers', 'ipv6_tunnel_network')
