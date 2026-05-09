"""add briefing settings

Revision ID: 62da15cd4b1f
Revises: 51da14cd4b0f
Create Date: 2026-05-09 11:47:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '62da15cd4b1f'
down_revision = '51da14cd4b0f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('milos', sa.Column('briefing_send_time', sa.String(), server_default='07:00', nullable=False))
    op.add_column('milos', sa.Column('briefing_enabled', sa.Boolean(), server_default='true', nullable=False))


def downgrade() -> None:
    op.drop_column('milos', 'briefing_enabled')
    op.drop_column('milos', 'briefing_send_time')
