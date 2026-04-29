from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models import Course, Lesson, Section
from app.schemas.content import CourseResponse, CourseStructure, LessonDetail

router = APIRouter(tags=["content"])


def sanitize_exercise_payload(
    exercise_type: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """Strip answer-revealing fields before exposing an exercise to the client.

    Multiple-choice answers (correct_index) and numeric answers (expected,
    tolerance) are evaluated server-side at submit time; the client only
    receives what's needed to render the question.
    """
    if exercise_type == "multiple_choice":
        return {"options": payload.get("options", [])}
    if exercise_type == "numeric":
        return {}
    return payload


async def _load_course(
    identifier: str,
    db: AsyncSession,
    *,
    with_structure: bool = False,
) -> Course:
    """Look up a course by UUID or by code (e.g. '4MM101'). 404 if neither matches."""
    try:
        course_id = UUID(identifier)
        stmt = select(Course).where(Course.id == course_id)
    except ValueError:
        stmt = select(Course).where(Course.code == identifier)

    if with_structure:
        stmt = stmt.options(
            selectinload(Course.sections).selectinload(Section.lessons)
        )

    course = (await db.execute(stmt)).scalar_one_or_none()
    if course is None:
        raise HTTPException(status_code=404, detail="course_not_found")
    return course


@router.get("/courses/{course_id_or_code}", response_model=CourseResponse)
async def get_course(
    course_id_or_code: str,
    db: AsyncSession = Depends(get_db),
) -> CourseResponse:
    course = await _load_course(course_id_or_code, db)
    return CourseResponse.model_validate(course)


@router.get(
    "/courses/{course_id_or_code}/structure",
    response_model=CourseStructure,
)
async def get_course_structure(
    course_id_or_code: str,
    db: AsyncSession = Depends(get_db),
) -> CourseStructure:
    course = await _load_course(course_id_or_code, db, with_structure=True)
    return CourseStructure.model_validate(course)


@router.get("/lessons/{lesson_id}", response_model=LessonDetail)
async def get_lesson(
    lesson_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> LessonDetail:
    stmt = (
        select(Lesson)
        .where(Lesson.id == lesson_id)
        .options(selectinload(Lesson.exercises))
    )
    lesson = (await db.execute(stmt)).scalar_one_or_none()
    if lesson is None:
        raise HTTPException(status_code=404, detail="lesson_not_found")

    return LessonDetail.model_validate(
        {
            "id": lesson.id,
            "order_index": lesson.order_index,
            "title": lesson.title,
            "description": lesson.description,
            "xp_reward": lesson.xp_reward,
            "exercises": [
                {
                    "id": ex.id,
                    "order_index": ex.order_index,
                    "exercise_type": ex.exercise_type,
                    "prompt": ex.prompt,
                    "explanation": ex.explanation,
                    "difficulty": ex.difficulty,
                    "payload": sanitize_exercise_payload(
                        ex.exercise_type, ex.payload
                    ),
                }
                for ex in lesson.exercises
            ],
        }
    )
