"""add chat_usage table

Revision ID: cc60b81c5a9e
Revises: 738170845fc1
Create Date: 2026-04-29 08:49:52.482465

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc60b81c5a9e'
down_revision: Union[str, Sequence[str], None] = '738170845fc1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'chat_usage',
        sa.Column(
            'id',
            sa.dialects.postgresql.UUID(as_uuid=True),
            server_default=sa.text('gen_random_uuid()'),
            nullable=False,
        ),
        sa.Column(
            'user_id',
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column('usage_date', sa.Date(), nullable=False),
        sa.Column(
            'message_count',
            sa.Integer(),
            server_default=sa.text('0'),
            nullable=False,
        ),
        sa.Column(
            'created_at',
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'], ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'user_id', 'usage_date', name='uq_chat_usage_user_date',
        ),
    )
    op.create_index(
        op.f('ix_chat_usage_usage_date'),
        'chat_usage',
        ['usage_date'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_chat_usage_usage_date'), table_name='chat_usage')
    op.drop_table('chat_usage')
