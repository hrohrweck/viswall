"""add mail_messages table for llm classification

Revision ID: c5534844c7e7
Revises: e1580e735101
Create Date: 2026-04-25 01:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c5534844c7e7'
down_revision: Union[str, None] = 'e1580e735101'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create mail_messages table
    op.create_table(
        'mail_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('domain_id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.String(length=255), nullable=False),
        sa.Column('sender', sa.String(length=255), nullable=False),
        sa.Column('recipients', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('subject', sa.String(length=500), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=True),
        sa.Column('body_preview', sa.Text(), nullable=True),
        sa.Column('spam_score', sa.Float(), nullable=True),
        sa.Column('virus_status', sa.String(length=20), nullable=True),
        sa.Column('llm_category', sa.String(length=50), nullable=True),
        sa.Column('llm_confidence', sa.Float(), nullable=True),
        sa.Column('llm_reason', sa.Text(), nullable=True),
        sa.Column('llm_provider', sa.String(length=20), nullable=True),
        sa.Column('llm_model', sa.String(length=50), nullable=True),
        sa.Column('classified_at', sa.DateTime(), nullable=True),
        sa.Column('action_taken', sa.String(length=20), nullable=True),
        sa.Column('action_reason', sa.Text(), nullable=True),
        sa.Column('action_taken_at', sa.DateTime(), nullable=True),
        sa.Column('action_taken_by', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('received_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('message_id'),
        sa.ForeignKeyConstraint(['domain_id'], ['mail_domains.id']),
        sa.ForeignKeyConstraint(['action_taken_by'], ['users.id'])
    )

    # Create indexes
    op.create_index('ix_mail_messages_domain_id', 'mail_messages', ['domain_id'])
    op.create_index('ix_mail_messages_llm_category', 'mail_messages', ['llm_category'])
    op.create_index('ix_mail_messages_status', 'mail_messages', ['status'])
    op.create_index('ix_mail_messages_received_at', 'mail_messages', ['received_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_mail_messages_received_at', table_name='mail_messages')
    op.drop_index('ix_mail_messages_status', table_name='mail_messages')
    op.drop_index('ix_mail_messages_llm_category', table_name='mail_messages')
    op.drop_index('ix_mail_messages_domain_id', table_name='mail_messages')

    # Drop table
    op.drop_table('mail_messages')
