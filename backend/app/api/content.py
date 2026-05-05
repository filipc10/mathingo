from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.dependencies import get_current_user
from app.models import (
    Course,
    DailyActivity,
    Exercise,
    ExerciseAttempt,
    Lesson,
    LessonAttempt,
    Section,
    Streak,
    User,
)
from app.schemas.content import (
    CourseProgressResponse,
    CourseResponse,
    CourseStructure,
    ExerciseCheckRequest,
    ExerciseCheckResponse,
    ExerciseResult,
    LessonDetail,
    ProgressInfo,
    ScoreSummary,
    SubmissionRequest,
    SubmissionResponse,
)

router = APIRouter(tags=["content"])


def sanitize_exercise_payload(
    exercise_type: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """Strip answer-revealing fields before exposing an exercise to the client.

    Each exercise type stores both its render data and its correct answer
    in the same JSONB column; everything that would leak the answer is
    removed here before the payload reaches the wire.
    """
    if exercise_type == "multiple_choice":
        return {"options": payload.get("options", [])}
    if exercise_type == "numeric":
        return {}
    if exercise_type == "cloze":
        return {"placeholder": payload.get("placeholder")}
    if exercise_type == "true_false":
        return {}
    if exercise_type == "matching":
        return {
            k: payload[k]
            for k in ("items", "categories", "instructions")
            if k in payload
        }
    if exercise_type == "step_ordering":
        return {
            k: payload[k]
            for k in ("steps", "instructions")
            if k in payload
        }
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


@router.get(
    "/courses/{course_id_or_code}/progress",
    response_model=CourseProgressResponse,
)
async def get_course_progress(
    course_id_or_code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CourseProgressResponse:
    course = await _load_course(course_id_or_code, db)

    # SELECT DISTINCT lesson_id FROM lesson_attempts WHERE user_id = me
    #   AND is_completed = true
    #   AND lesson_id IN (lessons of this course via section join)
    stmt = (
        select(LessonAttempt.lesson_id)
        .join(Lesson, Lesson.id == LessonAttempt.lesson_id)
        .join(Section, Section.id == Lesson.section_id)
        .where(LessonAttempt.user_id == current_user.id)
        .where(LessonAttempt.is_completed.is_(True))
        .where(Section.course_id == course.id)
        .distinct()
    )
    result = await db.execute(stmt)
    completed_lesson_ids = [row[0] for row in result.all()]

    return CourseProgressResponse(
        course_id=course.id,
        completed_lesson_ids=completed_lesson_ids,
    )


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

    if exercise.exercise_type == "cloze":
        if not isinstance(user_answer, str):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"answer_for_exercise_{exercise.id}_must_be_string",
            )
        expected = exercise.payload["value"]
        alternates = exercise.payload.get("alternates", [])
        case_sensitive = exercise.payload.get("case_sensitive", False)
        trim = exercise.payload.get("trim_whitespace", True)
        candidate = user_answer.strip() if trim else user_answer
        accepted = [expected, *alternates]
        if not case_sensitive:
            candidate = candidate.lower()
            accepted = [a.lower() for a in accepted]
        return candidate in accepted and candidate != "", expected

    if exercise.exercise_type == "true_false":
        # Strict bool — Python's bool is an int subclass, so without the
        # type check first an int 0/1 would silently match.
        if not isinstance(user_answer, bool):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"answer_for_exercise_{exercise.id}_must_be_boolean",
            )
        expected = exercise.payload["value"]
        return user_answer == expected, expected

    if exercise.exercise_type == "matching":
        if not isinstance(user_answer, dict):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"answer_for_exercise_{exercise.id}_must_be_object",
            )
        expected = exercise.payload["assignments"]
        return user_answer == expected, expected

    if exercise.exercise_type == "step_ordering":
        if not isinstance(user_answer, list):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"answer_for_exercise_{exercise.id}_must_be_array",
            )
        expected = exercise.payload["order"]
        return user_answer == expected, expected

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"unsupported_exercise_type_{exercise.exercise_type}",
    )


@router.post(
    "/exercises/{exercise_id}/check",
    response_model=ExerciseCheckResponse,
)
async def check_exercise_answer(
    exercise_id: UUID,
    request: ExerciseCheckRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExerciseCheckResponse:
    """Evaluate a single answer immediately, without persisting anything.

    Used by the lesson runner to show per-exercise feedback. Persistence
    (lesson_attempt, streak, daily_activity) still happens at lesson end via
    /lessons/{id}/submit, which re-evaluates server-side as defense-in-depth.
    """
    exercise = (
        await db.execute(select(Exercise).where(Exercise.id == exercise_id))
    ).scalar_one_or_none()
    if exercise is None:
        raise HTTPException(status_code=404, detail="exercise_not_found")

    is_correct, correct_answer = _evaluate(exercise, request.answer)
    return ExerciseCheckResponse(
        exercise_id=exercise.id,
        correct=is_correct,
        user_answer=request.answer,
        correct_answer=correct_answer,
        explanation=exercise.explanation,
    )


COMPLETION_THRESHOLD = 0.8


async def _persist_attempt_and_progress(
    *,
    db: AsyncSession,
    user: User,
    lesson: Lesson,
    correct_count: int,
    total_count: int,
    exercise_evaluations: list[tuple[Exercise, bool, Any]],
) -> tuple[bool, int, int, int]:
    """Insert lesson_attempt + N×exercise_attempts + streak + daily_activity.

    All writes share the outer SQLAlchemy session — if any one of them
    raises, FastAPI's dependency teardown rolls back the whole transaction
    so we never observe an inconsistent state (e.g. lesson_attempt without
    its exercise rows).

    Returns (is_lesson_completed, xp_earned, user_streak, user_xp_today).

    Race semantics: the partial UNIQUE on (user_id, lesson_id) WHERE
    is_completed=true permits at most one completed attempt per user-lesson.
    Two concurrent submits computing is_completed=true both try inserting;
    Postgres awards one and rejects the other with IntegrityError. The losing
    side falls back to is_completed=false, xp_earned=0 inside a savepoint so
    the outer transaction stays alive.
    """
    is_lesson_completed = (
        total_count > 0 and (correct_count / total_count) >= COMPLETION_THRESHOLD
    )

    # Has the user already earned XP for this lesson?
    already_completed_stmt = select(LessonAttempt.id).where(
        LessonAttempt.user_id == user.id,
        LessonAttempt.lesson_id == lesson.id,
        LessonAttempt.is_completed.is_(True),
    )
    already_completed = (
        await db.execute(already_completed_stmt)
    ).scalar_one_or_none() is not None

    db_is_completed = is_lesson_completed and not already_completed
    xp_earned = lesson.xp_reward if db_is_completed else 0

    now_ts = datetime.now(UTC)
    today = now_ts.date()
    attempt_kwargs: dict[str, Any] = {
        "user_id": user.id,
        "lesson_id": lesson.id,
        "correct_count": correct_count,
        "total_count": total_count,
        "started_at": now_ts,
        "finished_at": now_ts,
    }

    lesson_attempt = LessonAttempt(
        **attempt_kwargs,
        is_completed=db_is_completed,
        xp_earned=xp_earned,
    )
    try:
        async with db.begin_nested():
            db.add(lesson_attempt)
    except IntegrityError:
        # A concurrent submit beat us to the completed slot — record this
        # attempt as not-completed and earn no XP.
        db_is_completed = False
        xp_earned = 0
        lesson_attempt = LessonAttempt(
            **attempt_kwargs,
            is_completed=False,
            xp_earned=0,
        )
        db.add(lesson_attempt)
        await db.flush()
    else:
        await db.flush()

    # Bulk-insert exercise_attempts. This needs lesson_attempt.id, hence
    # the flush above. Denormalised columns (user_id, section_id, lesson_id,
    # exercise_type) make per-user / per-section / per-type aggregations
    # in the stats endpoint cheap.
    exercise_attempt_rows = [
        {
            "lesson_attempt_id": lesson_attempt.id,
            "exercise_id": exercise.id,
            "user_id": user.id,
            "exercise_type": exercise.exercise_type.value,
            "section_id": lesson.section_id,
            "lesson_id": lesson.id,
            "answer": {"value": user_answer},
            "is_correct": is_correct,
            "time_spent_ms": None,
        }
        for exercise, is_correct, user_answer in exercise_evaluations
    ]
    if exercise_attempt_rows:
        await db.execute(insert(ExerciseAttempt), exercise_attempt_rows)

    # Streak upsert (one row per user)
    streak = (
        await db.execute(select(Streak).where(Streak.user_id == user.id))
    ).scalar_one_or_none()
    if streak is None:
        streak = Streak(
            user_id=user.id,
            current_length=1,
            longest_length=1,
            last_active_date=today,
        )
        db.add(streak)
    else:
        prev = streak.last_active_date
        if prev == today:
            pass  # already counted today
        elif prev is not None and prev == today - timedelta(days=1):
            streak.current_length += 1
            if streak.current_length > streak.longest_length:
                streak.longest_length = streak.current_length
        else:
            # Gap or first activity ever — reset to 1 (today counts)
            streak.current_length = 1
            if streak.longest_length < 1:
                streak.longest_length = 1
        streak.last_active_date = today

    # DailyActivity upsert (one row per user-day)
    da_stmt = select(DailyActivity).where(
        DailyActivity.user_id == user.id,
        DailyActivity.activity_date == today,
    )
    daily = (await db.execute(da_stmt)).scalar_one_or_none()
    if daily is None:
        daily = DailyActivity(
            user_id=user.id,
            activity_date=today,
            xp_earned=xp_earned,
            lessons_completed=1 if db_is_completed else 0,
        )
        db.add(daily)
    else:
        daily.xp_earned += xp_earned
        if db_is_completed:
            daily.lessons_completed += 1

    await db.flush()
    await db.refresh(streak)
    await db.refresh(daily)

    return is_lesson_completed, xp_earned, streak.current_length, daily.xp_earned


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
    evaluations: list[tuple[Exercise, bool, Any]] = []
    correct_count = 0
    for ex in lesson.exercises:  # iteration order from order_index relationship
        user_answer = submissions_by_id[ex.id]
        is_correct, correct_answer = _evaluate(ex, user_answer)
        if is_correct:
            correct_count += 1
        evaluations.append((ex, is_correct, user_answer))
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

    is_lesson_completed, xp_earned, user_streak, user_xp_today = (
        await _persist_attempt_and_progress(
            db=db,
            user=current_user,
            lesson=lesson,
            correct_count=correct_count,
            total_count=total,
            exercise_evaluations=evaluations,
        )
    )
    await db.commit()

    return SubmissionResponse(
        lesson_id=lesson_id,
        results=results,
        score=ScoreSummary(
            correct_count=correct_count,
            total_count=total,
            all_correct=correct_count == total,
        ),
        progress=ProgressInfo(
            is_completed=is_lesson_completed,
            xp_earned=xp_earned,
            user_streak=user_streak,
            user_xp_today=user_xp_today,
        ),
    )
