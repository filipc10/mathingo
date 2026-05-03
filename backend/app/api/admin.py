"""Admin / debug endpoints.

Currently a single endpoint for manually firing a notification slot —
useful for testing the eligibility query and the push delivery path
without waiting for the cron schedule. Auth-required but not
admin-role gated; the MVP doesn't have roles, and a logged-in user
triggering "did the morning slot pick me?" is harmless. A real role
check would go here once roles exist.
"""

from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.dependencies import get_current_user
from app.models import User
from app.services.notification_service import process_notification_slot

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/notifications/trigger-now")
async def trigger_notification_slot_now(
    slot: Literal["morning", "noon", "evening"],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Manually run the eligibility scan for one slot.

    Returns counts so the caller can tell whether a notification was
    sent without poking the DB. UNIQUE on (user_id, sent_date,
    time_slot) makes this idempotent — calling twice within a slot's
    window does not produce duplicate pushes.
    """
    result = await process_notification_slot(slot, db)
    return {
        "slot": result.slot,
        "candidates": result.candidates,
        "sent": result.sent,
        "skipped_already_logged": result.skipped_already_logged,
        "failed": result.failed,
    }
