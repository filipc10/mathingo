"""Web Push delivery via VAPID.

Wraps pywebpush so call sites pass a domain object (PushSubscription)
plus a JSON-serialisable payload, and get back a boolean: True if sent,
False if the endpoint is gone (404/410) and the row should be deleted.

Other failures (network, 5xx, malformed VAPID) re-raise — the caller
decides whether to retry or surface the error.
"""

from __future__ import annotations

import json
import logging

from pywebpush import WebPushException, webpush

from app.config import settings
from app.models import PushSubscription

logger = logging.getLogger(__name__)


def send_push(subscription: PushSubscription, payload: dict) -> bool:
    """Send a push message. Return False if the subscription is gone."""
    if not settings.vapid_private_key:
        # Misconfigured environment — refuse rather than silently no-op,
        # which would mask the missing key in dev and prod alike.
        raise RuntimeError("VAPID_PRIVATE_KEY is not configured")

    try:
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {
                    "p256dh": subscription.p256dh,
                    "auth": subscription.auth,
                },
            },
            data=json.dumps(payload),
            vapid_private_key=settings.vapid_private_key,
            vapid_claims={"sub": settings.vapid_subject},
        )
        return True
    except WebPushException as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        if status in (404, 410):
            logger.info(
                "push subscription gone (status=%s), will be removed", status
            )
            return False
        logger.error("push send failed: status=%s exc=%s", status, exc)
        raise
