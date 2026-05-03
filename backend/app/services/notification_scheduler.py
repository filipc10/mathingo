"""Cron schedule for daily reminder slots.

Three fixed slots in UTC: 08:00 morning, 12:00 noon, 18:00 evening.
The hours sit safely outside the 22:00–08:00 sleep window — that
constraint is also enforced by `_assert_outside_sleep_window` so a
future config change can't accidentally wire a slot into the night.

The job store is in-memory: cron triggers are stateless (next-run
time recomputes from `now`), and lifespan re-registers everything on
startup, so we don't need SQLAlchemyJobStore persistence. Single
backend replica means single scheduler — no leader-election dance.
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.db import AsyncSessionLocal
from app.services.notification_service import process_notification_slot

logger = logging.getLogger(__name__)

SLOTS_UTC: dict[str, tuple[int, int]] = {
    "morning": (8, 0),
    "noon": (12, 0),
    "evening": (18, 0),
}

# Hard floor / ceiling for any slot the system will run. Anything that
# would fire inside [22:00, 08:00) UTC is rejected — pure guardrail,
# the current SLOTS_UTC values are all clear.
SLEEP_WINDOW_END_HOUR = 8
SLEEP_WINDOW_START_HOUR = 22


def _assert_outside_sleep_window(hour: int, minute: int) -> None:
    if hour < SLEEP_WINDOW_END_HOUR or hour >= SLEEP_WINDOW_START_HOUR:
        raise ValueError(
            f"slot {hour:02d}:{minute:02d} UTC falls inside the "
            f"{SLEEP_WINDOW_START_HOUR:02d}:00–{SLEEP_WINDOW_END_HOUR:02d}:00 "
            "sleep window and must not be scheduled"
        )


async def _run_slot(slot_name: str) -> None:
    async with AsyncSessionLocal() as db:
        result = await process_notification_slot(slot_name, db)
        logger.info(
            "slot=%s candidates=%d sent=%d skipped=%d failed=%d",
            result.slot,
            result.candidates,
            result.sent,
            result.skipped_already_logged,
            result.failed,
        )


def schedule_daily_jobs(scheduler: AsyncIOScheduler) -> None:
    for slot_name, (hour, minute) in SLOTS_UTC.items():
        _assert_outside_sleep_window(hour, minute)
        scheduler.add_job(
            _run_slot,
            CronTrigger(hour=hour, minute=minute, timezone="UTC"),
            args=[slot_name],
            id=f"notification_slot_{slot_name}",
            replace_existing=True,
            # If the job was supposed to fire while the worker was
            # rebooting, run it within the next 5 minutes instead of
            # silently skipping. After 5 minutes we'd rather wait for
            # tomorrow than push a noon reminder at 13:30.
            misfire_grace_time=300,
        )
        logger.info(
            "scheduled notification slot: %s at %02d:%02d UTC",
            slot_name,
            hour,
            minute,
        )
