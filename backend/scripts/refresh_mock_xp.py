"""Re-distribute weekly XP to the mock leaderboard users for the
current ISO week.

Run before each thesis demo so the weekly leaderboard is populated:

    docker compose exec backend python -m scripts.refresh_mock_xp

What it does:
- Computes Monday 00:00 UTC of the current week.
- For each mock user (email matches mock+%@mathingo.local), upserts
  a daily_activities row on Monday with the configured weekly XP and
  a rough lessons_completed count.
- Bumps streaks.last_active_date to today so the streak doesn't
  appear stale next to non-zero current_length.

Idempotent: re-running on the same day overwrites the same row
without creating duplicates (UPSERT on (user_id, activity_date)).
"""

from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db import AsyncSessionLocal
from app.models import DailyActivity, Streak, User

# (display_name suffix, weekly XP) — display_name is the lookup key.
MOCK_WEEKLY_XP: dict[str, int] = {
    "pavel-vse": 180,
    "karel-mat": 150,
    "marie-bp": 120,
    "tomas24": 95,
    "anna-dy": 80,
    "luki-mt": 65,
    "petra-vse": 50,
    "honza-mat": 30,
    "jana-st": 15,
}


def _week_start_utc() -> date:
    today = datetime.now(UTC).date()
    return today - timedelta(days=today.weekday())


async def main() -> None:
    week_start = _week_start_utc()
    today = datetime.now(UTC).date()

    async with AsyncSessionLocal() as session:
        users = (
            await session.execute(
                select(User).where(User.email.like("mock+%@mathingo.local"))
            )
        ).scalars().all()

        if not users:
            print("No mock users found. Did you run `alembic upgrade head`?")
            return

        for user in users:
            xp = MOCK_WEEKLY_XP.get(user.display_name)
            if xp is None:
                continue

            await session.execute(
                pg_insert(DailyActivity)
                .values(
                    user_id=user.id,
                    activity_date=week_start,
                    xp_earned=xp,
                    lessons_completed=max(1, xp // 15),
                )
                .on_conflict_do_update(
                    constraint="uq_daily_activities_user_date",
                    set_={
                        "xp_earned": xp,
                        "lessons_completed": max(1, xp // 15),
                    },
                )
            )

            # Refresh streak.last_active_date so the leaderboard view
            # doesn't show "active 8 days ago" next to a 7-day streak.
            streak = (
                await session.execute(
                    select(Streak).where(Streak.user_id == user.id)
                )
            ).scalar_one_or_none()
            if streak is not None and streak.current_length > 0:
                streak.last_active_date = today

        await session.commit()

    print(f"Refreshed weekly XP for {len(users)} mock users (week start {week_start}).")


if __name__ == "__main__":
    asyncio.run(main())
