"""fix sogo_user_view for mail users

Revision ID: 7383bc760d32
Revises: 742812ae405a
Create Date: 2026-07-05 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "7383bc760d32"
down_revision: Union[str, None] = "742812ae405a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP VIEW IF EXISTS sogo_user_view")
    op.execute("""
        CREATE VIEW sogo_user_view AS
        SELECT
            u.username || '@' || d.domain AS c_uid,
            u.username || '@' || d.domain AS c_name,
            u.password_hash AS c_password,
            COALESCE(u.full_name, u.username || '@' || d.domain) AS c_cn,
            u.username || '@' || d.domain AS mail
        FROM mail_users u
        JOIN mail_domains d ON u.domain_id = d.id
        WHERE u.enabled = true AND d.enabled = true
    """)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS sogo_user_view")
    op.execute("""
        CREATE VIEW sogo_user_view AS
        SELECT
            username AS c_uid,
            username AS c_name,
            password_hash AS c_password,
            COALESCE(email, username) AS c_cn,
            COALESCE(email, username || '@localhost') AS mail
        FROM users
        WHERE is_active = true
    """)
