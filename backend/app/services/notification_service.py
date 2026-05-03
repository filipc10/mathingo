"""Daily reminder eligibility + send orchestration.

`process_notification_slot` is the single entry point used by both the
APScheduler cron job and the manual admin trigger. The flow:

  1. Find candidate users — opted in for this slot, no XP today, has
     at least one push subscription, not already notified for this
     slot today.
  2. For each candidate: pick a fresh template, INSERT a log row
     (status=pending) up front so the UNIQUE constraint protects
     against duplicate cron firings, then send to every subscription
     and finally UPDATE the log row with the outcome.

INSERT-before-send is intentional defence-in-depth: a second cron
run (or a manual trigger racing with the scheduled one) hits the
UNIQUE on `(user_id, sent_date, time_slot)` and exits without ever
calling pywebpush.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    DailyActivity,
    NotificationLog,
    NotificationPreferences,
    PushSubscription,
    User,
)
from app.services.notification_texts import pick_notification_text
from app.services.push_service import send_push

logger = logging.getLogger(__name__)


@dataclass
class SlotRunResult:
    slot: str
    candidates: int
    sent: int
    skipped_already_logged: int
    failed: int


async def process_notification_slot(
    slot_name: str, db: AsyncSession
) -> SlotRunResult:
    today = datetime.now(UTC).date()

    # Users who already earned XP today — skip them, they don't need
    # the nudge. Coalesce check is xp_earned > 0 (a row with 0 XP is
    # treated as "no activity").
    has_activity_today = (
        select(DailyActivity.user_id)
        .where(
            and_(
                DailyActivity.activity_date == today,
                DailyActivity.xp_earned > 0,
            )
        )
        .scalar_subquery()
    )

    # Users already notified for this slot today — idempotence guard
    # at query level (the UNIQUE constraint is the real safety net,
    # this just avoids spurious IntegrityError noise in logs).
    already_notified = (
        select(NotificationLog.user_id)
        .where(
            and_(
                NotificationLog.sent_date == today,
                NotificationLog.time_slot == slot_name,
            )
        )
        .scalar_subquery()
    )

    has_subscription = (
        select(PushSubscription.id)
        .where(PushSubscription.user_id == User.id)
        .exists()
    )

    stmt = (
        select(User)
        .join(NotificationPreferences, NotificationPreferences.user_id == User.id)
        .where(
            NotificationPreferences.enabled.is_(True),
            NotificationPreferences.time_slot == slot_name,
            User.id.notin_(has_activity_today),
            User.id.notin_(already_notified),
            has_subscription,
        )
    )

    candidates = (await db.execute(stmt)).scalars().all()
    logger.info("slot=%s candidates=%d", slot_name, len(candidates))

    sent = 0
    skipped = 0
    failed = 0
    for user in candidates:
        outcome = await _send_to_user(user, slot_name, today, db)
        if outcome == "sent":
            sent += 1
        elif outcome == "already_logged":
            skipped += 1
        else:
            failed += 1

    return SlotRunResult(
        slot=slot_name,
        candidates=len(candidates),
        sent=sent,
        skipped_already_logged=skipped,
        failed=failed,
    )


async def _send_to_user(
    user: User, slot_name: str, today, db: AsyncSession
) -> str:
    """Send to one user. Returns 'sent' | 'failed' | 'already_logged'."""
    recent_rows = await db.execute(
        select(NotificationLog.text_used).where(
            NotificationLog.user_id == user.id,
            NotificationLog.sent_date >= today - timedelta(days=7),
        )
    )
    recent_templates = [r[0] for r in recent_rows.all()]

    copy = pick_notification_text(user, recent_templates)

    log_row = NotificationLog(
        user_id=user.id,
        sent_date=today,
        time_slot=slot_name,
        text_used=copy.template,
        push_status="pending",
    )
    db.add(log_row)
    try:
        await db.flush()
    except IntegrityError:
        # Another runner won the race — exit without sending.
        await db.rollback()
        logger.info(
            "user=%s slot=%s already logged for %s, skipping",
            user.id,
            slot_name,
            today,
        )
        return "already_logged"

    subs_result = await db.execute(
        select(PushSubscription).where(PushSubscription.user_id == user.id)
    )
    subscriptions = list(subs_result.scalars().all())

    sent_any = False
    for sub in subscriptions:
        try:
            ok = send_push(
                sub,
                {
                    "title": copy.title,
                    "body": copy.body,
                    "url": "/learn",
                },
            )
            if ok:
                sent_any = True
            else:
                # Subscription gone (404/410). Drop the row so we don't
                # keep paying push-service round-trips for a dead endpoint.
                await db.delete(sub)
        except Exception:
            logger.exception("push send failed for sub=%s", sub.id)

    log_row.push_status = "sent" if sent_any else "failed"
    await db.commit()
    return "sent" if sent_any else "failed"
