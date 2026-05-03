"""Push subscription endpoint tests.

Avoid hitting real push services — send_push is monkey-patched in the
one test that exercises POST /push/test. Subscribe / unsubscribe /
upsert paths run against the live dev Postgres, since the database
behaviour (UNIQUE constraint, ON CONFLICT) is the part worth testing.
"""

from uuid import uuid4

import pytest
from sqlalchemy import select

from app.config import settings
from app.models import PushSubscription


pytestmark = pytest.mark.asyncio


def _fake_subscription_payload(suffix: str = "abc") -> dict:
    return {
        "endpoint": f"https://fcm.googleapis.com/fcm/send/fake-{suffix}",
        "keys": {"p256dh": f"p256dh-{suffix}", "auth": f"auth-{suffix}"},
        "device_label": "Test Device",
        "user_agent": "pytest",
    }


async def test_vapid_public_key_returns_configured_key(client):
    response = await client.get("/push/vapid-public-key")
    if not settings.vapid_public_key:
        # Misconfigured env (no VAPID set) — endpoint must surface that
        # rather than return an empty string we'd happily push with.
        assert response.status_code == 503
        return
    assert response.status_code == 200
    assert response.json() == {"key": settings.vapid_public_key}


async def test_subscribe_inserts_row(client, test_user, db_session):
    payload = _fake_subscription_payload(suffix=uuid4().hex[:8])
    response = await client.post("/push/subscribe", json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "ok"

    rows = (
        await db_session.execute(
            select(PushSubscription).where(
                PushSubscription.user_id == test_user.id,
                PushSubscription.endpoint == payload["endpoint"],
            )
        )
    ).scalars().all()
    assert len(rows) == 1
    assert rows[0].p256dh == payload["keys"]["p256dh"]
    assert rows[0].device_label == "Test Device"


async def test_resubscribe_upserts_existing_row(client, test_user, db_session):
    suffix = uuid4().hex[:8]
    first = _fake_subscription_payload(suffix=suffix)
    second = {
        **first,
        "keys": {"p256dh": "rotated-p256dh", "auth": "rotated-auth"},
        "device_label": "Test Device Renamed",
    }

    r1 = await client.post("/push/subscribe", json=first)
    r2 = await client.post("/push/subscribe", json=second)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["subscription_id"] == r2.json()["subscription_id"]

    rows = (
        await db_session.execute(
            select(PushSubscription).where(
                PushSubscription.user_id == test_user.id,
                PushSubscription.endpoint == first["endpoint"],
            )
        )
    ).scalars().all()
    assert len(rows) == 1
    assert rows[0].p256dh == "rotated-p256dh"
    assert rows[0].auth == "rotated-auth"
    assert rows[0].device_label == "Test Device Renamed"
    assert rows[0].last_used_at is not None


async def test_unsubscribe_removes_row(client, test_user, db_session):
    payload = _fake_subscription_payload(suffix=uuid4().hex[:8])
    await client.post("/push/subscribe", json=payload)

    response = await client.delete(
        "/push/subscribe", params={"endpoint": payload["endpoint"]}
    )
    assert response.status_code == 200

    rows = (
        await db_session.execute(
            select(PushSubscription).where(
                PushSubscription.user_id == test_user.id,
                PushSubscription.endpoint == payload["endpoint"],
            )
        )
    ).scalars().all()
    assert rows == []


async def test_test_push_404_when_no_subscriptions(client):
    response = await client.post("/push/test")
    assert response.status_code == 404
    assert response.json()["detail"] == "no_subscriptions"


async def test_test_push_prunes_gone_subscriptions(
    client, test_user, db_session, monkeypatch
):
    """When send_push returns False (404/410), the row must be deleted."""
    payload = _fake_subscription_payload(suffix=uuid4().hex[:8])
    await client.post("/push/subscribe", json=payload)

    # Simulate the endpoint being gone — send_push lives in app.api.push's
    # namespace once imported, so patch it there.
    from app.api import push as push_module

    monkeypatch.setattr(push_module, "send_push", lambda sub, body: False)

    response = await client.post("/push/test")
    assert response.status_code == 200
    body = response.json()
    assert body["sent"] == 0
    assert body["total"] >= 1

    # Subscription should have been deleted.
    rows = (
        await db_session.execute(
            select(PushSubscription).where(
                PushSubscription.user_id == test_user.id,
                PushSubscription.endpoint == payload["endpoint"],
            )
        )
    ).scalars().all()
    assert rows == []
