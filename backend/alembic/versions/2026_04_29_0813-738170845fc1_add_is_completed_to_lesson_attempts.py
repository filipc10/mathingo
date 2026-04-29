"""add is_completed to lesson_attempts

Revision ID: 738170845fc1
Revises: f4ed5e40904a
Create Date: 2026-04-29 08:13:20.880795

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '738170845fc1'
down_revision: Union[str, Sequence[str], None] = 'f4ed5e40904a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Backfill existing rows with is_completed=false via server_default,
    # then drop the default — application code is the only writer going
    # forward and supplies the value explicitly.
    op.add_column(
        'lesson_attempts',
        sa.Column(
            'is_completed',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.alter_column('lesson_attempts', 'is_completed', server_default=None)
    op.create_index(
        'uq_lesson_attempts_user_lesson_completed',
        'lesson_attempts',
        ['user_id', 'lesson_id'],
        unique=True,
        postgresql_where=sa.text('is_completed = true'),
    )


def downgrade() -> None:
    op.drop_index(
        'uq_lesson_attempts_user_lesson_completed',
        table_name='lesson_attempts',
        postgresql_where=sa.text('is_completed = true'),
    )
    op.drop_column('lesson_attempts', 'is_completed')
