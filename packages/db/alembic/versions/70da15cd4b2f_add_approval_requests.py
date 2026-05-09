"""add approval_requests

Revision ID: 70da15cd4b2f
Revises: 62da15cd4b1f
Create Date: 2026-05-09 17:34:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '70da15cd4b2f'
down_revision: Union[str, None] = '62da15cd4b1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('approval_requests',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('milo_id', sa.UUID(), nullable=False),
        sa.Column('thread_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('options_jsonb', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('context_payload_jsonb', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('urgency', sa.String(), nullable=False, server_default='medium'),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('response_notes', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['milo_id'], ['milos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['thread_id'], ['threads.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('approval_requests')
