"""add_llm_provider_registry_tables

Revision ID: d4a8f2e1b3c0
Revises: 5125192c673e
Create Date: 2026-04-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd4a8f2e1b3c0'
down_revision: Union[str, None] = '5125192c673e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # llm_providers
    op.create_table(
        'llm_providers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('provider_type', sa.String(length=20), nullable=False),
        sa.Column('base_url', sa.String(length=500), nullable=True),
        sa.Column('api_key', sa.String(length=500), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # llm_models
    op.create_table(
        'llm_models',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('provider_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('max_tokens', sa.Integer(), nullable=True),
        sa.Column('supports_vision', sa.Boolean(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['provider_id'], ['llm_providers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # llm_use_case_configs
    op.create_table(
        'llm_use_case_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('use_case', sa.String(length=50), nullable=False),
        sa.Column('provider_id', sa.Integer(), nullable=True),
        sa.Column('model_id', sa.Integer(), nullable=True),
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('max_tokens', sa.Integer(), nullable=True),
        sa.Column('top_p', sa.Float(), nullable=True),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('timeout_seconds', sa.Integer(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['provider_id'], ['llm_providers.id']),
        sa.ForeignKeyConstraint(['model_id'], ['llm_models.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('use_case')
    )

    # Seed default Ollama provider + qwen3.5:9b model + use-case configs
    op.execute("""
        INSERT INTO llm_providers (id, name, provider_type, base_url, is_enabled, is_default, created_at, updated_at)
        VALUES (1, 'Local Ollama', 'ollama', 'http://ollama:11434', true, true, NOW(), NOW())
    """)

    op.execute("""
        INSERT INTO llm_models (id, provider_id, name, display_name, description, max_tokens, is_enabled, created_at)
        VALUES (1, 1, 'qwen3.5:9b', 'Qwen 3.5 9B', 'Default local model for classification and assistance', 4096, true, NOW())
    """)

    op.execute("""
        INSERT INTO llm_use_case_configs (use_case, provider_id, model_id, temperature, max_tokens, system_prompt, timeout_seconds, is_enabled, created_at, updated_at)
        VALUES
            ('email_classification', 1, 1, 0.1, 200, 'You are an email classification assistant. Respond only with valid JSON.', 30, true, NOW(), NOW()),
            ('assistant_chat', 1, 1, 0.3, 500, 'You are a helpful network security assistant.', 30, true, NOW(), NOW()),
            ('security_audit', 1, 1, 0.2, 1000, 'You are a security audit expert. Analyze configurations for vulnerabilities.', 60, true, NOW(), NOW())
    """)


def downgrade() -> None:
    op.drop_table('llm_use_case_configs')
    op.drop_table('llm_models')
    op.drop_table('llm_providers')
