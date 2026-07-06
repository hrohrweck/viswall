"""add_mail_aliases

Revision ID: aa11bb22cc33
Revises: bd213a2f9c31
Create Date: 2026-07-04 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "aa11bb22cc33"
down_revision: Union[str, None] = "bd213a2f9c31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mail_aliases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("domain_id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("destination", sa.String(length=255), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["domain_id"], ["mail_domains.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mail_aliases_domain_id", "mail_aliases", ["domain_id"], unique=False)
    op.create_index("ix_mail_aliases_source", "mail_aliases", ["source"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_mail_aliases_source", table_name="mail_aliases")
    op.drop_index("ix_mail_aliases_domain_id", table_name="mail_aliases")
    op.drop_table("mail_aliases")
