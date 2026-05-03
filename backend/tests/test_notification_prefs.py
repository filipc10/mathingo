"""User-facing notification preferences endpoint tests.

GET lazy-creates a row, PATCH updates fields partially, the time_slot
literal rejects unknown values at the schema layer (422), and the
has_push_subscription flag tracks the underlying subscription rows
without a separate fetch.
"""

from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models import NotificationPreferences, PushSubscription


pytestmark = pytest.mark.asyncio


async def test_get_lazy_creates_row(client, test_user, db_session):
    response = await client.get("/users/me/notifications")
    assert response.status_code == 200
    body = response.json()
    assert body["enabled"] is False
    assert body["time_slot"] == "morning"
    assert body["has_push_subscription"] is False

    # The endpoint must have persisted the row, not just returned a
    # default in memory.
    rows = (
        await db_session.execute(
            select(NotificationPreferences).where(
                NotificationPreferences.user_id == test_user.id
            )
        )
    ).scalars().all()
    assert len(rows) == 1


async def test_patch_enabled(client, test_user, db_session):
    res = await client.patch(
        "/users/me/notifications", json={"enabled": True}
    )
    assert res.status_code == 200
    assert res.json()["enabled"] is True

    row = (
        await db_session.execute(
            select(NotificationPreferences).where(
                NotificationPreferences.user_id == test_user.id
            )
        )
    ).scalar_one()
    assert row.enabled is True


async def test_patch_time_slot(client, test_user, db_session):
    res = await client.patch(
        "/users/me/notifications", json={"time_slot": "evening"}
    )
    assert res.status_code == 200
    assert res.json()["time_slot"] == "evening"

    row = (
        await db_session.execute(
            select(NotificationPreferences).where(
                NotificationPreferences.user_id == test_user.id
            )
        )
    ).scalar_one()
    assert row.time_slot == "evening"


async def test_patch_combined(client, test_user, db_session):
    res = await client.patch(
        "/users/me/notifications",
        json={"enabled": True, "time_slot": "noon"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["enabled"] is True
    assert body["time_slot"] == "noon"


async def test_patch_invalid_time_slot_rejected(client):
    res = await client.patch(
        "/users/me/notifications", json={"time_slot": "midnight"}
    )
    assert res.status_code == 422


async def test_patch_empty_body_is_idempotent(client, test_user, db_session):
    # First seed a known state.
    await client.patch(
        "/users/me/notifications", json={"enabled": True, "time_slot": "noon"}
    )
    # An empty PATCH should leave it alone.
    res = await client.patch("/users/me/notifications", json={})
    assert res.status_code == 200
    body = res.json()
    assert body["enabled"] is True
    assert body["time_slot"] == "noon"


async def test_has_push_subscription_reflects_subscription_rows(
    client, test_user, db_session
):
    initial = await client.get("/users/me/notifications")
    assert initial.json()["has_push_subscription"] is False

    db_session.add(
        PushSubscription(
            user_id=test_user.id,
            endpoint=f"https://fcm.googleapis.com/fcm/send/{uuid4().hex}",
            p256dh="p",
            auth="a",
            device_label="Test",
        )
    )
    await db_session.commit()

    after = await client.get("/users/me/notifications")
    assert after.json()["has_push_subscription"] is True
