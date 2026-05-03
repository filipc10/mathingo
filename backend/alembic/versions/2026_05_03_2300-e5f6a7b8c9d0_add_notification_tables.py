"""add notification preferences and logs

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-05-03 23:00:00.000000

Two tables go in together because the daily-reminder feature can't
function without both — preferences gate who is eligible, logs enforce
the one-per-day cap and feed the anti-repetition pool.

Defaults are deliberately conservative: enabled=false on
notification_preferences means a fresh row never sends push until the
user explicitly flips it on. The backfill at the end gives every
existing user (Filip + nine seeded mocks) the same opt-in default,
so the rollout doesn't suddenly start pushing to anyone who hasn't
been asked.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notification_preferences",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "time_slot",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'morning'"),
        ),
        sa.Column(
            "daily_max",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", name="uq_notification_preferences_user"),
        sa.CheckConstraint(
            "time_slot IN ('morning', 'noon', 'evening')",
            name="ck_notification_preferences_time_slot",
        ),
    )

    op.create_table(
        "notification_logs",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "sent_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("sent_date", sa.Date(), nullable=False),
        sa.Column("time_slot", sa.String(length=20), nullable=False),
        sa.Column("text_used", sa.Text(), nullable=False),
        sa.Column(
            "push_status",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.UniqueConstraint(
            "user_id",
            "sent_date",
            "time_slot",
            name="uq_notification_logs_user_date_slot",
        ),
    )
    op.create_index(
        "ix_notification_logs_user_date",
        "notification_logs",
        ["user_id", "sent_date"],
    )

    # Backfill defaults for every existing user. ON CONFLICT DO NOTHING
    # so re-running the upgrade (or running on a DB that was partly
    # backfilled by some earlier hot-fix) is a no-op.
    op.execute(
        """
        INSERT INTO notification_preferences (user_id, enabled, time_slot, daily_max)
        SELECT id, false, 'morning', 1 FROM users
        ON CONFLICT (user_id) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_index(
        "ix_notification_logs_user_date", table_name="notification_logs"
    )
    op.drop_table("notification_logs")
    op.drop_table("notification_preferences")
