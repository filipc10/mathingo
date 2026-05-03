"""Push subscription lifecycle.

The browser owns the subscription URL; we just remember it so we can
deliver messages later. POST /push/subscribe is upsert-shaped (browsers
sometimes rotate p256dh/auth without changing the endpoint), DELETE is
straight removal, and POST /push/test is a self-targeted smoke test —
useful in dev and for users to confirm that delivery works after they
grant permission.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.config import settings
from app.db import get_db
from app.dependencies import get_current_user
from app.models import PushSubscription, User
from app.schemas.push import (
    SubscribeRequest,
    SubscribeResponse,
    TestPushResponse,
    UnsubscribeResponse,
    VapidPublicKeyResponse,
)
from app.services.push_service import send_push

router = APIRouter(prefix="/push", tags=["push"])


@router.get("/vapid-public-key", response_model=VapidPublicKeyResponse)
async def get_vapid_public_key() -> VapidPublicKeyResponse:
    """Return the server's VAPID public key.

    Public by definition — the browser feeds it into pushManager.subscribe
    as `applicationServerKey`. No auth required.
    """
    if not settings.vapid_public_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="vapid_not_configured",
        )
    return VapidPublicKeyResponse(key=settings.vapid_public_key)


@router.post("/subscribe", response_model=SubscribeResponse)
async def subscribe_push(
    payload: SubscribeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubscribeResponse:
    stmt = (
        pg_insert(PushSubscription)
        .values(
            user_id=current_user.id,
            endpoint=payload.endpoint,
            p256dh=payload.keys.p256dh,
            auth=payload.keys.auth,
            device_label=payload.device_label,
            user_agent=payload.user_agent,
        )
        .on_conflict_do_update(
            index_elements=["user_id", "endpoint"],
            set_={
                "p256dh": payload.keys.p256dh,
                "auth": payload.keys.auth,
                "device_label": payload.device_label,
                "user_agent": payload.user_agent,
                "last_used_at": func.now(),
            },
        )
        .returning(PushSubscription.id)
    )
    result = await db.execute(stmt)
    sub_id = result.scalar_one()
    await db.commit()
    return SubscribeResponse(subscription_id=sub_id)


@router.delete("/subscribe", response_model=UnsubscribeResponse)
async def unsubscribe_push(
    endpoint: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UnsubscribeResponse:
    await db.execute(
        delete(PushSubscription).where(
            PushSubscription.user_id == current_user.id,
            PushSubscription.endpoint == endpoint,
        )
    )
    await db.commit()
    return UnsubscribeResponse()


@router.post("/test", response_model=TestPushResponse)
async def send_test_push(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TestPushResponse:
    """Send a test notification to every subscription the caller owns.

    Self-targeted only — current_user is read from the cookie and that's
    the only user we ever push to. Doubles as a debug endpoint and as the
    user-facing "test" button in a future settings UI.
    """
    subs = (
        await db.execute(
            select(PushSubscription).where(
                PushSubscription.user_id == current_user.id
            )
        )
    ).scalars().all()

    if not subs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="no_subscriptions"
        )

    payload = {
        "title": "Mathingo",
        "body": "Test notifikace funguje 🎉",
        "url": "/learn",
    }

    sent = 0
    for sub in subs:
        ok = send_push(sub, payload)
        if ok:
            sent += 1
        else:
            await db.delete(sub)

    await db.commit()
    return TestPushResponse(sent=sent, total=len(subs))
