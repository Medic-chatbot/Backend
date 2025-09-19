"""
Add last_recommendation_message_id to chat_rooms for windowed context

Revision ID: 005_add_chatroom_pivot
Revises: 004_disease_equipment
Create Date: 2025-09-13
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_add_chatroom_pivot'
down_revision = '004_disease_equipment'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'chat_rooms',
        sa.Column('last_recommendation_message_id', sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('chat_rooms', 'last_recommendation_message_id')
