"""Widen metric_snapshots byte counters to BigInteger.

The memory/disk byte columns were INTEGER (int32, max ~2.1 GB). Realistic
values (8 GB memory, 100 GB disk) overflow int32, so every snapshot insert
failed with "value out of int32 range" and the dashboards stayed empty.

Also backfills llm_models booleans left NULL by the original registry seed
(the ORM-side default never applied to raw INSERTs), which made
GET /admin/llm/models fail response validation with a 500.

Revision ID: a7c91d4e2f50
Revises: e8f1a3b5c7d9
Create Date: 2026-10-05
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a7c91d4e2f50"
# Re-parented onto the mta-forwarding migration: PR #61 and PR #60 both
# branched from 7383bc760d32, which left two heads after both merged and
# made `alembic upgrade head` fail (production rollback, 2026-10-09).
down_revision = "e8f1a3b5c7d9"
branch_labels = None
depends_on = None

_BYTE_COLUMNS = (
    "memory_used_bytes",
    "memory_total_bytes",
    "disk_used_bytes",
    "disk_total_bytes",
)


def upgrade() -> None:
    for column in _BYTE_COLUMNS:
        op.alter_column(
            "metric_snapshots",
            column,
            existing_type=sa.Integer(),
            type_=sa.BigInteger(),
            existing_nullable=True,
        )

    op.execute("UPDATE llm_models SET supports_vision = false WHERE supports_vision IS NULL")
    op.execute("UPDATE llm_models SET is_enabled = true WHERE is_enabled IS NULL")
    op.alter_column(
        "llm_models",
        "supports_vision",
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=sa.false(),
    )
    op.alter_column(
        "llm_models",
        "is_enabled",
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=sa.true(),
    )


def downgrade() -> None:
    op.alter_column(
        "llm_models",
        "is_enabled",
        existing_type=sa.Boolean(),
        nullable=True,
        server_default=None,
    )
    op.alter_column(
        "llm_models",
        "supports_vision",
        existing_type=sa.Boolean(),
        nullable=True,
        server_default=None,
    )
    for column in _BYTE_COLUMNS:
        op.alter_column(
            "metric_snapshots",
            column,
            existing_type=sa.BigInteger(),
            type_=sa.Integer(),
            existing_nullable=True,
        )
