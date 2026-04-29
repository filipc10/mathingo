from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.dependencies import get_current_user
from app.models import Course, Exercise, Lesson, Section, User
from app.schemas.content import (
    CourseResponse,
    CourseStructure,
    ExerciseResult,
    LessonDetail,
    ScoreSummary,
    SubmissionRequest,
    SubmissionResponse,
)

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


def _evaluate(exercise: Exercise, user_answer: Any) -> tuple[bool, Any]:
    """Return (is_correct, correct_answer) for the given exercise + user answer.

    Raises 422 if the user's answer type doesn't match the exercise type.
    Note that Python's bool is a subclass of int, so we reject booleans
    explicitly — `isinstance(True, int)` is True but accepting True/False
    as a multiple-choice index would be a confusing footgun.
    """
    if exercise.exercise_type == "multiple_choice":
        if isinstance(user_answer, bool) or not isinstance(user_answer, int):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"answer_for_exercise_{exercise.id}_must_be_integer",
            )
        correct_index = exercise.payload["correct_index"]
        return user_answer == correct_index, correct_index

    if exercise.exercise_type == "numeric":
        if isinstance(user_answer, bool) or not isinstance(
            user_answer, (int, float)
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"answer_for_exercise_{exercise.id}_must_be_number",
            )
        expected = exercise.payload["expected"]
        tolerance = exercise.payload.get("tolerance", 0.001)
        return abs(user_answer - expected) <= tolerance, expected

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"unsupported_exercise_type_{exercise.exercise_type}",
    )


@router.post(
    "/lessons/{lesson_id}/submit",
    response_model=SubmissionResponse,
)
async def submit_lesson_answers(
    lesson_id: UUID,
    request: SubmissionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubmissionResponse:
    stmt = (
        select(Lesson)
        .where(Lesson.id == lesson_id)
        .options(selectinload(Lesson.exercises))
    )
    lesson = (await db.execute(stmt)).scalar_one_or_none()
    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="lesson_not_found"
        )

    expected_ids = {ex.id for ex in lesson.exercises}
    submitted_ids = {a.exercise_id for a in request.answers}
    if expected_ids != submitted_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="answers_must_match_lesson_exercises",
        )

    submissions_by_id: dict[UUID, Any] = {
        a.exercise_id: a.answer for a in request.answers
    }

    results: list[ExerciseResult] = []
    correct_count = 0
    for ex in lesson.exercises:  # iteration order from order_index relationship
        user_answer = submissions_by_id[ex.id]
        is_correct, correct_answer = _evaluate(ex, user_answer)
        if is_correct:
            correct_count += 1
        results.append(
            ExerciseResult(
                exercise_id=ex.id,
                correct=is_correct,
                user_answer=user_answer,
                correct_answer=correct_answer,
                explanation=ex.explanation,
            )
        )

    total = len(results)
    return SubmissionResponse(
        lesson_id=lesson_id,
        results=results,
        score=ScoreSummary(
            correct_count=correct_count,
            total_count=total,
            all_correct=correct_count == total,
        ),
    )
