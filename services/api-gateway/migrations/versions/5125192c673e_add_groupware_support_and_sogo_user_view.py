"""add groupware support and sogo_user_view

Revision ID: 5125192c673e
Revises: c5534844c7e7
Create Date: 2026-04-25 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '5125192c673e'
down_revision: Union[str, None] = 'c5534844c7e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add groupware_enabled column to mail_domains
    op.add_column(
        'mail_domains',
        sa.Column('groupware_enabled', sa.Boolean(), nullable=True, default=False)
    )

    # Create sogo_user_view for SOGo SQL authentication
    op.execute("""
        CREATE OR REPLACE VIEW sogo_user_view AS
        SELECT
            username AS c_uid,
            username AS c_name,
            password_hash AS c_password,
            COALESCE(email, username) AS c_cn,
            COALESCE(email, username || '@localhost') AS mail
        FROM users
        WHERE is_active = true;
    """)

    # Grant permissions to sogo user if it exists
    # Note: This will fail if the sogo user doesn't exist, which is fine during migration
    # The actual user creation happens in docker-compose or manual setup
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'sogo') THEN
                GRANT SELECT ON sogo_user_view TO sogo;
            END IF;
        END
        $$;
    """)


def downgrade() -> None:
    # Drop the view
    op.execute("DROP VIEW IF EXISTS sogo_user_view")

    # Drop the column
    op.drop_column('mail_domains', 'groupware_enabled')
