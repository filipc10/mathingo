"""Smoke tests for the v2 seed of the Limity funkce section.

Hits the live dev DB through the API rather than re-running the seed —
the migration already ran via `alembic upgrade head` when the dev
container started.
"""

import pytest


@pytest.mark.asyncio
async def test_limity_funkce_section_has_five_lessons(client):
    resp = await client.get("/courses/4MM101/structure")
    assert resp.status_code == 200

    sections = resp.json()["sections"]
    limity = next((s for s in sections if s["title"] == "Limity funkce"), None)
    assert limity is not None, "Limity funkce section missing"
    assert len(limity["lessons"]) == 5


@pytest.mark.asyncio
async def test_limity_funkce_has_thirty_exercises(client):
    structure = (await client.get("/courses/4MM101/structure")).json()
    limity = next(s for s in structure["sections"] if s["title"] == "Limity funkce")

    total = 0
    for lesson_summary in limity["lessons"]:
        detail = (await client.get(f"/lessons/{lesson_summary['id']}")).json()
        total += len(detail["exercises"])
    assert total == 30


@pytest.mark.asyncio
async def test_limity_funkce_uses_all_required_types(client):
    structure = (await client.get("/courses/4MM101/structure")).json()
    limity = next(s for s in structure["sections"] if s["title"] == "Limity funkce")

    seen_types: set[str] = set()
    for lesson_summary in limity["lessons"]:
        detail = (await client.get(f"/lessons/{lesson_summary['id']}")).json()
        for ex in detail["exercises"]:
            seen_types.add(ex["exercise_type"])

    # Every type the new seed promises has at least one example.
    assert {
        "multiple_choice",
        "numeric",
        "true_false",
        "matching",
        "step_ordering",
    } <= seen_types
