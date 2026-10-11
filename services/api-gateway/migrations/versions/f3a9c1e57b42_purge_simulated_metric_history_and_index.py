"""purge simulated metric history and index snapshots

Revision ID: f3a9c1e57b42
Revises: a7c91d4e2f50
Create Date: 2026-10-11

Every row written into metric_snapshots before real collection existed is
simulated: system/network metrics were random until the psutil-based
collector (#69) and mail counters still are. This migration deletes that
history so dashboards only ever show real telemetry, and adds the
(instance_id, timestamp) index the retention pruner and time-range
queries rely on.

The purge is not reversible — downgrading only drops the index.
"""

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f3a9c1e57b42"
down_revision: str = "a7c91d4e2f50"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DELETE FROM metric_snapshots")
    op.create_index(
        "ix_metric_snapshots_instance_timestamp",
        "metric_snapshots",
        ["instance_id", "timestamp"],
    )


def downgrade() -> None:
    op.drop_index("ix_metric_snapshots_instance_timestamp", table_name="metric_snapshots")
