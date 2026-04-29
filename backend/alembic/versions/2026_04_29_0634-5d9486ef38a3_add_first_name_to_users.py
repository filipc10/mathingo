"""add first_name to users

Revision ID: 5d9486ef38a3
Revises: 0fcdeb013033
Create Date: 2026-04-29 06:34:45.750814

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5d9486ef38a3'
down_revision: Union[str, Sequence[str], None] = '0fcdeb013033'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add column with server_default='' so existing rows backfill cleanly.
    op.add_column(
        'users',
        sa.Column('first_name', sa.String(length=40), nullable=False, server_default=''),
    )
    # Drop the server_default so future inserts must supply the value
    # explicitly — the model declares default="" on the Python side, the
    # application layer is the only writer.
    op.alter_column('users', 'first_name', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'first_name')
