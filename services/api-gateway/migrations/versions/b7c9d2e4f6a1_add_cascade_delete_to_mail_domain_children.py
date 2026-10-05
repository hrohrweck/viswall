"""add cascade delete to mail domain children

Revision ID: b7c9d2e4f6a1
Revises: 7383bc760d32
Create Date: 2026-10-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7c9d2e4f6a1"
down_revision: Union[str, None] = "7383bc760d32"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # mail_users.domain_id → mail_domains.id
    op.drop_constraint("mail_users_domain_id_fkey", "mail_users", type_="foreignkey")
    op.create_foreign_key(
        "mail_users_domain_id_fkey",
        "mail_users",
        "mail_domains",
        ["domain_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # mail_messages.domain_id → mail_domains.id
    op.drop_constraint("mail_messages_domain_id_fkey", "mail_messages", type_="foreignkey")
    op.create_foreign_key(
        "mail_messages_domain_id_fkey",
        "mail_messages",
        "mail_domains",
        ["domain_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # mail_aliases.domain_id → mail_domains.id
    op.drop_constraint("mail_aliases_domain_id_fkey", "mail_aliases", type_="foreignkey")
    op.create_foreign_key(
        "mail_aliases_domain_id_fkey",
        "mail_aliases",
        "mail_domains",
        ["domain_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("mail_aliases_domain_id_fkey", "mail_aliases", type_="foreignkey")
    op.create_foreign_key(
        "mail_aliases_domain_id_fkey",
        "mail_aliases",
        "mail_domains",
        ["domain_id"],
        ["id"],
    )

    op.drop_constraint("mail_messages_domain_id_fkey", "mail_messages", type_="foreignkey")
    op.create_foreign_key(
        "mail_messages_domain_id_fkey",
        "mail_messages",
        "mail_domains",
        ["domain_id"],
        ["id"],
    )

    op.drop_constraint("mail_users_domain_id_fkey", "mail_users", type_="foreignkey")
    op.create_foreign_key(
        "mail_users_domain_id_fkey",
        "mail_users",
        "mail_domains",
        ["domain_id"],
        ["id"],
    )
