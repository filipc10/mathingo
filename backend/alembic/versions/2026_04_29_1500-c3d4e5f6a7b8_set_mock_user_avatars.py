"""set varied avatars for mock leaderboard users

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-29 15:00:00.000000

The earlier add_avatar_fields_to_users migration backfilled every existing
user with beam/blue defaults. For the leaderboard demo screenshots in the
thesis we want the nine mock users to look visually distinct, so this
migration assigns each one a unique (variant, palette) pair. Real users
keep their beam/blue defaults until they pick something during onboarding.

Idempotent: re-running re-applies the same UPDATEs (no-op if values already
match). The downgrade resets all mock rows back to beam/blue.
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (email, variant, palette)
MOCK_AVATARS = [
    ("mock+pavel@mathingo.local", "marble", "green"),
    ("mock+karel@mathingo.local", "pixel", "purple"),
    ("mock+marie@mathingo.local", "beam", "sunset"),
    ("mock+tomas@mathingo.local", "sunset", "blue"),
    ("mock+anna@mathingo.local", "ring", "purple"),
    ("mock+lukas@mathingo.local", "bauhaus", "mono"),
    ("mock+petra@mathingo.local", "marble", "blue"),
    ("mock+honza@mathingo.local", "pixel", "green"),
    ("mock+jana@mathingo.local", "beam", "mono"),
]


def upgrade() -> None:
    for email, variant, palette in MOCK_AVATARS:
        op.execute(
            f"""
            UPDATE users
            SET avatar_variant = '{variant}', avatar_palette = '{palette}'
            WHERE email = '{email}'
            """
        )


def downgrade() -> None:
    op.execute(
        """
        UPDATE users
        SET avatar_variant = 'beam', avatar_palette = 'blue'
        WHERE email LIKE 'mock+%@mathingo.local'
        """
    )
