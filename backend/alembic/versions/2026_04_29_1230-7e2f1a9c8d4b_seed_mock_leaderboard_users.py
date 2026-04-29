"""seed mock leaderboard users

Revision ID: 7e2f1a9c8d4b
Revises: cc60b81c5a9e
Create Date: 2026-04-29 12:30:00.000000

Inserts nine mock Czech users + their streak rows, used purely to fill
the leaderboard for thesis demo screenshots. Their emails sit on the
non-existent @mathingo.local domain so they can never receive a magic
link if someone tries to sign in as one.

Daily-activity rows (the actual XP) are NOT created here on purpose:
weekly XP is time-relative ("this week"), and a value baked into a
migration would silently rot to zero after one calendar week. The
companion script `backend/scripts/refresh_mock_xp.py` repopulates
daily_activities for the current week — run it before each demo.

Idempotent via ON CONFLICT DO NOTHING on the unique columns.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import insert as pg_insert

# revision identifiers, used by Alembic.
revision: str = "7e2f1a9c8d4b"
down_revision: Union[str, Sequence[str], None] = "cc60b81c5a9e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


MOCK_USERS = [
    ("mock+pavel@mathingo.local", "pavel-vse", "Pavel", 7),
    ("mock+karel@mathingo.local", "karel-mat", "Karel", 5),
    ("mock+marie@mathingo.local", "marie-bp", "Marie", 3),
    ("mock+tomas@mathingo.local", "tomas24", "Tomáš", 2),
    ("mock+anna@mathingo.local", "anna-dy", "Anna", 4),
    ("mock+lukas@mathingo.local", "luki-mt", "Lukáš", 1),
    ("mock+petra@mathingo.local", "petra-vse", "Petra", 1),
    ("mock+honza@mathingo.local", "honza-mat", "Honza", 0),
    ("mock+jana@mathingo.local", "jana-st", "Jana", 0),
]


def upgrade() -> None:
    bind = op.get_bind()

    users = sa.table(
        "users",
        sa.column("id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.column("email", sa.String),
        sa.column("display_name", sa.String),
        sa.column("first_name", sa.String),
        sa.column("daily_xp_goal", sa.Integer),
    )
    streaks = sa.table(
        "streaks",
        sa.column("user_id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.column("current_length", sa.Integer),
        sa.column("longest_length", sa.Integer),
        sa.column("last_active_date", sa.Date),
    )

    today = sa.func.current_date()

    for email, display_name, first_name, streak in MOCK_USERS:
        # Upsert user — ON CONFLICT DO NOTHING returns no row if it
        # already exists, so we follow up with an explicit SELECT to
        # recover the id either way.
        bind.execute(
            pg_insert(users)
            .values(
                email=email,
                display_name=display_name,
                first_name=first_name,
                daily_xp_goal=20,
            )
            .on_conflict_do_nothing(index_elements=["email"])
        )
        user_id = bind.execute(
            sa.select(users.c.id).where(users.c.email == email)
        ).scalar()
        assert user_id is not None  # row was inserted or already existed

        bind.execute(
            pg_insert(streaks)
            .values(
                user_id=user_id,
                current_length=streak,
                longest_length=streak,
                last_active_date=today,
            )
            .on_conflict_do_nothing(index_elements=["user_id"])
        )


def downgrade() -> None:
    # CASCADE on users.id removes streaks + daily_activities for these
    # mock rows, so no extra cleanup is needed.
    op.execute(
        "DELETE FROM users WHERE email LIKE 'mock+%@mathingo.local'"
    )
