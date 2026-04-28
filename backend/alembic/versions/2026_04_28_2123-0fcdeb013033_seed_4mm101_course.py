"""seed 4mm101 course

Revision ID: 0fcdeb013033
Revises: d35b3a02feb9
Create Date: 2026-04-28 21:23:48.276272

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0fcdeb013033'
down_revision: Union[str, Sequence[str], None] = 'd35b3a02feb9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Insert the 4MM101 course row used as the default for new users."""
    op.execute(
        """
        INSERT INTO courses (code, title, description)
        VALUES (
            '4MM101',
            'Matematika pro informatiky a statistiky',
            'Základní kurz matematiky na VŠE — analýza, lineární algebra, '
            'kombinatorika a pravděpodobnost.'
        )
        ON CONFLICT (code) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM courses WHERE code = '4MM101'")
