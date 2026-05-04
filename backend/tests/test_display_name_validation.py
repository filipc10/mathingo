"""Display name regex enforcement on PATCH /users/me.

Spaces, diacritics, emoji, and special characters must 422; the
allowed alphabet is `^[A-Za-z0-9_.-]+$` between 3 and 30 chars.
"""

import pytest


pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize(
    "value",
    [
        "with space",
        "diakritikaěščřž",
        "emoji😀here",
        "ahoj!",
        "tag#1",
        "ab",  # too short
        "a" * 31,  # too long
    ],
)
async def test_invalid_display_name_rejected(client, value):
    res = await client.patch("/users/me", json={"display_name": value})
    assert res.status_code == 422


@pytest.mark.parametrize(
    "shape",
    [
        "{}",  # plain
        "{}-tag",
        "{}.dot",
        "{}_42",
        "ABC{}",
        "a-{}.c_d",
    ],
)
async def test_valid_display_name_accepted(client, shape):
    # Generate per-case to dodge the seeded leaderboard mock display names
    # (luki-mt etc.) which would 409 the test on a collision.
    from uuid import uuid4

    value = shape.format(uuid4().hex[:6])
    res = await client.patch("/users/me", json={"display_name": value})
    assert res.status_code == 200, res.text
