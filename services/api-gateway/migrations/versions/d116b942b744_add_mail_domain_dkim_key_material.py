"""add mail domain dkim key material

Revision ID: d116b942b744
Revises: cd52fd4f0cd2
Create Date: 2026-11-08 13:45:09.567922

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd116b942b744'
down_revision: Union[str, None] = 'cd52fd4f0cd2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('mail_domains', sa.Column('dkim_selector', sa.String(length=63), server_default='viswall', nullable=False))
    op.add_column('mail_domains', sa.Column('dkim_public_key', sa.Text(), nullable=True))
    op.add_column('mail_domains', sa.Column('dkim_private_key', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('mail_domains', 'dkim_private_key')
    op.drop_column('mail_domains', 'dkim_public_key')
    op.drop_column('mail_domains', 'dkim_selector')
