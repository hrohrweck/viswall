"""widen_mail_quota_bytes

Revision ID: 742812ae405a
Revises: aa11bb22cc33
Create Date: 2026-07-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "742812ae405a"
down_revision: Union[str, None] = "aa11bb22cc33"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "mail_users",
        "quota_bytes",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=True,
        postgresql_using="quota_bytes::bigint",
    )
    op.alter_column(
        "mail_users",
        "quota_used",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=True,
        postgresql_using="quota_used::bigint",
    )


def downgrade() -> None:
    op.alter_column(
        "mail_users",
        "quota_used",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=True,
        postgresql_using="quota_used::integer",
    )
    op.alter_column(
        "mail_users",
        "quota_bytes",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=True,
        postgresql_using="quota_bytes::integer",
    )
