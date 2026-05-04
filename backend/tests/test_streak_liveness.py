"""Streak liveness rule — display value goes to zero once the chain
breaks, even though the DB row is only fixed on the next lesson submit.
"""

from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from app.services.streak import effective_streak


@pytest.mark.parametrize(
    "last_active_offset_days,expected",
    [
        (0, 5),  # active today → keep
        (-1, 5),  # active yesterday → still alive
        (-2, 0),  # gap → broken
        (-7, 0),  # week-old → broken
    ],
)
def test_effective_streak_window(last_active_offset_days, expected):
    today = date(2026, 5, 4)
    streak = SimpleNamespace(
        current_length=5,
        last_active_date=today + timedelta(days=last_active_offset_days),
    )
    assert effective_streak(streak, today) == expected


def test_effective_streak_no_row():
    today = date(2026, 5, 4)
    assert effective_streak(None, today) == 0


def test_effective_streak_null_date():
    today = date(2026, 5, 4)
    streak = SimpleNamespace(current_length=3, last_active_date=None)
    assert effective_streak(streak, today) == 0
