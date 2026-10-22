"""vpn server site-to-site client tunnel fields

Revision ID: cd52fd4f0cd2
Revises: 866c6f4a7ebf
Create Date: 2026-10-22 23:26:58.984239

Adds the site-to-site / client tunnel fields to vpn_servers:

  - tunnel_type           (String, nullable) - server|client|site-to-site;
                          python-side default "server" (no server_default, so
                          existing rows stay NULL and are treated as legacy
                          "server" rows — no tunnel is default-enabled)
  - endpoint              (String, nullable) - remote host:port
  - peer_public_key       (String, nullable) - remote WireGuard public key
  - allowed_ips           (String, nullable) - e.g. "10.80.0.0/16"
  - persistent_keepalive  (Integer, nullable) - python-side default 25
  - local_address         (String, nullable) - local tunnel address
  - private_key           (String, nullable) - client/site-to-site tunnels
                          ONLY; plaintext at rest in Postgres (same posture
                          as Instance.api_key today). NEVER commit real key
                          material (this file contains none).

All columns are nullable; existing rows are untouched (no backfill, no
data loss, no drops). Hand-reviewed: autogenerate also proposed the same
pre-existing drift as todo 21 (llm_models provider FK recreate,
ix_mail_aliases_source, metric_snapshots instance FK, qos_policies
interface FK) which is out of scope for this migration and was removed.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cd52fd4f0cd2'
down_revision: Union[str, None] = '866c6f4a7ebf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('vpn_servers', sa.Column('tunnel_type', sa.String(length=20), nullable=True))
    op.add_column('vpn_servers', sa.Column('endpoint', sa.String(length=255), nullable=True))
    op.add_column('vpn_servers', sa.Column('peer_public_key', sa.String(length=255), nullable=True))
    op.add_column('vpn_servers', sa.Column('allowed_ips', sa.String(length=500), nullable=True))
    op.add_column('vpn_servers', sa.Column('persistent_keepalive', sa.Integer(), nullable=True))
    op.add_column('vpn_servers', sa.Column('local_address', sa.String(length=45), nullable=True))
    op.add_column('vpn_servers', sa.Column('private_key', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('vpn_servers', 'private_key')
    op.drop_column('vpn_servers', 'local_address')
    op.drop_column('vpn_servers', 'persistent_keepalive')
    op.drop_column('vpn_servers', 'allowed_ips')
    op.drop_column('vpn_servers', 'peer_public_key')
    op.drop_column('vpn_servers', 'endpoint')
    op.drop_column('vpn_servers', 'tunnel_type')
