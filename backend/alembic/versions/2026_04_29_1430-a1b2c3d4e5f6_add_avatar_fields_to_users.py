"""add avatar fields to users

Revision ID: a1b2c3d4e5f6
Revises: 7e2f1a9c8d4b
Create Date: 2026-04-29 14:30:00.000000

Adds avatar_variant and avatar_palette to users. Both are NOT NULL with
server defaults so existing rows get the same baseline avatar (beam/blue);
defaults are then dropped so future inserts must specify explicit values
(onboarding form is the source of truth post-migration). Check constraints
guard the allowed value sets at the DB level.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "7e2f1a9c8d4b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


AVATAR_VARIANTS = ("marble", "beam", "pixel", "sunset", "ring", "bauhaus")
AVATAR_PALETTES = ("blue", "green", "purple", "sunset", "mono")


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "avatar_variant",
            sa.String(length=20),
            nullable=False,
            server_default="beam",
        ),
    )
    op.alter_column("users", "avatar_variant", server_default=None)
    op.create_check_constraint(
        "ck_users_avatar_variant",
        "users",
        "avatar_variant IN ('marble', 'beam', 'pixel', 'sunset', 'ring', 'bauhaus')",
    )

    op.add_column(
        "users",
        sa.Column(
            "avatar_palette",
            sa.String(length=20),
            nullable=False,
            server_default="blue",
        ),
    )
    op.alter_column("users", "avatar_palette", server_default=None)
    op.create_check_constraint(
        "ck_users_avatar_palette",
        "users",
        "avatar_palette IN ('blue', 'green', 'purple', 'sunset', 'mono')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_users_avatar_palette", "users", type_="check")
    op.drop_column("users", "avatar_palette")
    op.drop_constraint("ck_users_avatar_variant", "users", type_="check")
    op.drop_column("users", "avatar_variant")
