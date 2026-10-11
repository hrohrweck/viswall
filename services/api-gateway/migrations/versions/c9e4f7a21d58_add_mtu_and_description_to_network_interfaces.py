"""add mtu and description to network_interfaces

Revision ID: c9e4f7a21d58
Revises: f3a9c1e57b42
Create Date: 2026-10-11

The node agent relays interface desired state to the host; MTU and a
free-form description are part of the managed configuration surface.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c9e4f7a21d58"
down_revision: str = "f3a9c1e57b42"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "network_interfaces",
        sa.Column("mtu", sa.Integer(), nullable=True),
    )
    op.add_column(
        "network_interfaces",
        sa.Column("description", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("network_interfaces", "description")
    op.drop_column("network_interfaces", "mtu")
