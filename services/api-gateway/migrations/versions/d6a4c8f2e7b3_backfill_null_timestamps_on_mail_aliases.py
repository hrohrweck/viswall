"""backfill null timestamps on mail_aliases

Legacy aliases imported via raw SQL (migrate_legacy_mail.py) predate the
ORM's Python-side datetime defaults and have NULL created_at/updated_at.
MailAliasResponse requires both, so one legacy row made the whole alias
list endpoint return 500. Backfill the missing timestamps.

Revision ID: d6a4c8f2e7b3
Revises: b7c9d2e4f6a1
Create Date: 2026-10-05 12:45:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "d6a4c8f2e7b3"
down_revision: Union[str, None] = "b7c9d2e4f6a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE mail_aliases "
        "SET created_at = COALESCE(created_at, now()), "
        "    updated_at = COALESCE(updated_at, now()) "
        "WHERE created_at IS NULL OR updated_at IS NULL"
    )


def downgrade() -> None:
    # Data repair only — nothing to revert.
    pass
