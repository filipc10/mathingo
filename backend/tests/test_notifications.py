"""Notification logic tests.

Three layers:
  1. vocative — pure function, table-driven.
  2. pick_notification_text — anti-repetition + name substitution,
     pinned RNG so the assertion is deterministic.
  3. process_notification_slot — DB-backed eligibility against the
     dev Postgres, send_push monkey-patched so we don't touch FCM.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models import (
    DailyActivity,
    NotificationLog,
    NotificationPreferences,
    PushSubscription,
)
from app.services.notification_service import process_notification_slot
from app.services.notification_texts import (
    NEUTRAL,
    QUESTION,
    WITH_NAME,
    pick_notification_text,
)
from app.services.vocative import vocative


pytestmark = pytest.mark.asyncio


# ---------- vocative ----------


@pytest.mark.parametrize(
    "name,expected",
    [
        ("Filip", "Filipe"),
        ("Pavel", "Pavle"),
        ("Anna", "Anno"),
        ("Tomáš", "Tomáši"),
        ("Marie", "Marie"),
        ("Petr", "Petře"),
        ("", ""),
        ("A", "A"),
    ],
)
async def test_vocative(name, expected):
    assert vocative(name) == expected


# ---------- pick_notification_text ----------


async def test_pick_substitutes_vocative_in_with_name(test_user):
    test_user.first_name = "Filip"
    rng = random.Random(0)
    # First template after seeding RNG with 0 is deterministic; we
    # sweep the seed space to find one that returns a with_name line
    # so the assertion is stable regardless of pool reordering.
    seen_with_name = False
    for seed in range(200):
        copy = pick_notification_text(test_user, [], rng=random.Random(seed))
        if copy.template in WITH_NAME:
            assert "Filipe" in copy.body
            assert "{name}" not in copy.body
            assert copy.template != copy.body  # rendered != template
            seen_with_name = True
            break
    assert seen_with_name, "RNG sweep never picked a with_name line — pool issue"


async def test_pick_skips_recently_used_templates(test_user):
    # Block 17 of 18 templates; the 18th must be the result regardless of seed.
    pool = [*WITH_NAME, *NEUTRAL, *QUESTION]
    target = pool[7]  # arbitrary
    blocked = [t for t in pool if t != target]
    copy = pick_notification_text(test_user, blocked, rng=random.Random(0))
    assert copy.template == target


async def test_pick_falls_back_when_pool_exhausted(test_user):
    # Every template recently used → picker still has to return something.
    pool = [*WITH_NAME, *NEUTRAL, *QUESTION]
    copy = pick_notification_text(test_user, pool, rng=random.Random(1))
    assert copy.template in pool


# ---------- process_notification_slot ----------


async def _enable_prefs(db_session, user, *, slot="morning") -> None:
    """Upsert preferences row to (enabled=True, slot=…)."""
    existing = (
        await db_session.execute(
            select(NotificationPreferences).where(
                NotificationPreferences.user_id == user.id
            )
        )
    ).scalar_one_or_none()
    if existing is None:
        db_session.add(
            NotificationPreferences(
                user_id=user.id, enabled=True, time_slot=slot, daily_max=1
            )
        )
    else:
        existing.enabled = True
        existing.time_slot = slot
    await db_session.commit()


async def _add_subscription(db_session, user) -> PushSubscription:
    sub = PushSubscription(
        user_id=user.id,
        endpoint=f"https://fcm.googleapis.com/fcm/send/test-{uuid4().hex}",
        p256dh="p256dh-test",
        auth="auth-test",
        device_label="Test",
    )
    db_session.add(sub)
    await db_session.commit()
    return sub


async def test_eligible_user_gets_logged_and_sent(
    db_session, test_user, monkeypatch
):
    await _enable_prefs(db_session, test_user)
    await _add_subscription(db_session, test_user)

    from app.services import notification_service as svc

    monkeypatch.setattr(svc, "send_push", lambda sub, payload: True)

    result = await process_notification_slot("morning", db_session)
    assert result.candidates >= 1
    assert result.sent >= 1

    log = (
        await db_session.execute(
            select(NotificationLog).where(NotificationLog.user_id == test_user.id)
        )
    ).scalar_one()
    assert log.time_slot == "morning"
    assert log.push_status == "sent"


async def test_user_with_activity_today_is_skipped(
    db_session, test_user, monkeypatch
):
    await _enable_prefs(db_session, test_user)
    await _add_subscription(db_session, test_user)

    today = datetime.now(UTC).date()
    db_session.add(
        DailyActivity(
            user_id=test_user.id,
            activity_date=today,
            xp_earned=20,
            lessons_completed=1,
        )
    )
    await db_session.commit()

    from app.services import notification_service as svc

    monkeypatch.setattr(svc, "send_push", lambda sub, payload: True)

    await process_notification_slot("morning", db_session)
    rows = (
        await db_session.execute(
            select(NotificationLog).where(NotificationLog.user_id == test_user.id)
        )
    ).scalars().all()
    assert rows == []  # no log row created for an already-active user


async def test_user_without_subscription_is_skipped(db_session, test_user):
    await _enable_prefs(db_session, test_user)
    # No PushSubscription added — the `exists(...)` clause should drop us.

    await process_notification_slot("morning", db_session)
    rows = (
        await db_session.execute(
            select(NotificationLog).where(NotificationLog.user_id == test_user.id)
        )
    ).scalars().all()
    assert rows == []


async def test_double_trigger_does_not_duplicate_log(
    db_session, test_user, monkeypatch
):
    await _enable_prefs(db_session, test_user)
    await _add_subscription(db_session, test_user)

    from app.services import notification_service as svc

    monkeypatch.setattr(svc, "send_push", lambda sub, payload: True)

    first = await process_notification_slot("morning", db_session)
    second = await process_notification_slot("morning", db_session)

    assert first.sent == 1
    # Second run sees the user via "already_notified" subquery and
    # excludes them from candidates, so sent is 0 and no second log row.
    assert second.sent == 0
    assert second.candidates == 0

    rows = (
        await db_session.execute(
            select(NotificationLog).where(
                NotificationLog.user_id == test_user.id,
                NotificationLog.sent_date == datetime.now(UTC).date(),
                NotificationLog.time_slot == "morning",
            )
        )
    ).scalars().all()
    assert len(rows) == 1


async def test_recent_log_blocks_template(db_session, test_user, monkeypatch):
    """A log row inside the 7-day window must keep its template out of the picker."""
    await _enable_prefs(db_session, test_user)
    await _add_subscription(db_session, test_user)

    # Plant a 2-day-old log row using a known template.
    yesterday = datetime.now(UTC).date() - timedelta(days=2)
    blocked_template = WITH_NAME[0]
    db_session.add(
        NotificationLog(
            user_id=test_user.id,
            sent_date=yesterday,
            time_slot="morning",
            text_used=blocked_template,
            push_status="sent",
        )
    )
    await db_session.commit()

    from app.services import notification_service as svc

    monkeypatch.setattr(svc, "send_push", lambda sub, payload: True)

    await process_notification_slot("morning", db_session)

    today_log = (
        await db_session.execute(
            select(NotificationLog).where(
                NotificationLog.user_id == test_user.id,
                NotificationLog.sent_date == datetime.now(UTC).date(),
            )
        )
    ).scalar_one()
    assert today_log.text_used != blocked_template
