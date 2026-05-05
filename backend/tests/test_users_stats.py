"""Smoke tests for GET /users/me/stats.

Two cases:
 1. Zero state — fresh user with no attempts: counters are zero, sections
    list still includes the full 4MM101 roadmap with zero stats per lesson.
 2. Happy path — submit one lesson, then verify per-type / per-section /
    per-lesson aggregates reflect the recorded answers.
"""

from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Course, Exercise, Lesson, Section


pytestmark = pytest.mark.asyncio


async def test_stats_zero_state_returns_full_roadmap(client, test_user, db_session):
    response = await client.get("/users/me/stats")
    assert response.status_code == 200
    body = response.json()

    assert body["total_xp"] == 0
    assert body["current_streak"] == 0
    assert body["longest_streak"] == 0
    assert body["lessons_completed"] == 0
    assert body["total_exercise_attempts"] == 0
    assert body["overall_winrate"] == 0.0
    assert body["by_type"] == []
    assert body["last_active_date"] is None

    if test_user.course_id is not None:
        # Sections must include the full 4MM101 roadmap, even with zero attempts.
        course = (
            await db_session.execute(
                select(Course)
                .where(Course.id == test_user.course_id)
                .options(selectinload(Course.sections))
            )
        ).scalar_one()
        assert len(body["sections"]) == len(course.sections)
        for section in body["sections"]:
            assert section["attempted"] == 0
            assert section["correct_attempts"] == 0
            assert section["winrate"] == 0.0
            for lesson in section["lessons"]:
                assert lesson["total_attempts"] == 0
                assert lesson["is_completed"] is False


async def _pick_first_lesson(db_session) -> Lesson | None:
    course = (
        await db_session.execute(select(Course).where(Course.code == "4MM101"))
    ).scalar_one_or_none()
    if course is None:
        return None
    section = (
        await db_session.execute(
            select(Section)
            .where(Section.course_id == course.id)
            .options(selectinload(Section.lessons).selectinload(Lesson.exercises))
            .order_by(Section.order_index)
        )
    ).scalars().first()
    if section is None or not section.lessons:
        return None
    for lesson in sorted(section.lessons, key=lambda lvl: lvl.order_index):
        if lesson.exercises:
            return lesson
    return None


async def test_stats_happy_path_after_submit(client, test_user, db_session):
    lesson = await _pick_first_lesson(db_session)
    if lesson is None:
        pytest.skip("4MM101 course not seeded in dev DB")

    # Build correct answers for every exercise in the lesson — this way
    # we get a guaranteed completion (≥66%), 100% winrate, and per-type
    # rows in the response.
    payload_answers: list[dict[str, Any]] = []
    for ex in sorted(lesson.exercises, key=lambda e: e.order_index):
        if ex.exercise_type.value == "multiple_choice":
            answer = ex.payload["correct_index"]
        elif ex.exercise_type.value == "numeric":
            answer = ex.payload["expected"]
        else:
            pytest.skip(f"unsupported exercise_type {ex.exercise_type}")
        payload_answers.append({"exercise_id": str(ex.id), "answer": answer})

    submit = await client.post(
        f"/lessons/{lesson.id}/submit", json={"answers": payload_answers}
    )
    assert submit.status_code == 200, submit.text
    submit_body = submit.json()
    assert submit_body["progress"]["is_completed"] is True

    response = await client.get("/users/me/stats")
    assert response.status_code == 200
    body = response.json()

    assert body["total_exercise_attempts"] == len(payload_answers)
    assert body["overall_winrate"] == 1.0
    assert body["lessons_completed"] == 1
    assert body["current_streak"] >= 1
    assert body["total_xp"] == lesson.xp_reward

    # Per-type — we should see at least one entry, all winrate 1.0
    type_summary = {row["exercise_type"]: row for row in body["by_type"]}
    expected_types = {ex.exercise_type.value for ex in lesson.exercises}
    assert set(type_summary.keys()) == expected_types
    for entry in type_summary.values():
        assert entry["winrate"] == 1.0
        assert entry["correct_attempts"] == entry["total_attempts"]

    # Per-lesson — find the lesson we submitted, check aggregates
    target_lesson_stats = None
    for section in body["sections"]:
        for lesson_stats in section["lessons"]:
            if lesson_stats["lesson_id"] == str(lesson.id):
                target_lesson_stats = lesson_stats
                break
    assert target_lesson_stats is not None
    assert target_lesson_stats["is_completed"] is True
    assert target_lesson_stats["best_score"] == 1.0
    assert target_lesson_stats["winrate"] == 1.0
    assert target_lesson_stats["total_attempts"] == len(payload_answers)
