"""add mta forwarding to mail domains

Revision ID: e8f1a3b5c7d9
Revises: d6a4c8f2e7b3
Create Date: 2026-10-05 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e8f1a3b5c7d9"
down_revision: Union[str, None] = "d6a4c8f2e7b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "mail_domains",
        sa.Column(
            "mta_forward_enabled",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
    )
    op.add_column(
        "mail_domains",
        sa.Column("mta_forward_host", sa.String(255), nullable=True),
    )
    op.add_column(
        "mail_domains",
        sa.Column(
            "mta_forward_port",
            sa.Integer(),
            server_default="25",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("mail_domains", "mta_forward_port")
    op.drop_column("mail_domains", "mta_forward_host")
    op.drop_column("mail_domains", "mta_forward_enabled")
