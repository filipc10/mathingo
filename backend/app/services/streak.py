"""Streak liveness rules.

A `Streak` row stores the *last known* current_length, written when the
user completes a lesson. Reads have to apply the liveness rule on top:
the chain is alive only if the last activity is today or yesterday
(UTC). Anything older means the chain broke between writes — show 0
until the next lesson submit fixes the row.

Keeping the rule on the read side avoids a separate scheduled "reset
streak rows at midnight" job. The DB value stays stale until the user
practices again, at which point the existing submit-side logic
(content.py: prev != today-1 → reset to 1) writes the correct value.
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import case
from sqlalchemy.sql.elements import ColumnElement

from app.models import Streak


def effective_streak(streak: Streak | None, today: date) -> int:
    """Return current_length only if the streak is still alive."""
    if streak is None or streak.last_active_date is None:
        return 0
    if streak.last_active_date < today - timedelta(days=1):
        return 0
    return streak.current_length


def effective_streak_sql(today: date) -> ColumnElement[int]:
    """SQL expression with the same liveness rule for use in queries.

    Used by the leaderboard sort + display so a user with a stale
    `current_length` doesn't outrank a user who actually practiced
    yesterday.
    """
    yesterday = today - timedelta(days=1)
    return case(
        (Streak.last_active_date.is_(None), 0),
        (Streak.last_active_date < yesterday, 0),
        else_=Streak.current_length,
    )
