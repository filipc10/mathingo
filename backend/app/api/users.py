"""User-scoped endpoints — currently stats only.

The /auth/me endpoint stays in app/api/auth.py because it's part of the
session lifecycle ("who am I"). Profile-page reads (/users/me/stats) and
profile-page writes (/users/me PATCH, added in a later commit) live here
because they're feature endpoints, not auth state.
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.dependencies import get_current_user
from app.models import (
    Course,
    DailyActivity,
    ExerciseAttempt,
    Lesson,
    LessonAttempt,
    Section,
    Streak,
    User,
)
from app.schemas.user import LessonStats, SectionStats, TypeStats, UserStats

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/stats", response_model=UserStats)
async def get_my_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserStats:
    """Aggregate stats for the profile page.

    Multiple small queries instead of one CTE — at thesis-tier sizes
    (a few thousand exercise_attempts per user) the difference is
    negligible and the code stays legible. The expensive part is the
    course-structure read; everything else is indexed lookups on
    (user_id, ...) composite indexes.
    """
    # 1. Streak row (current + longest + last active)
    streak = (
        await db.execute(select(Streak).where(Streak.user_id == current_user.id))
    ).scalar_one_or_none()
    current_streak = streak.current_length if streak else 0
    longest_streak = streak.longest_length if streak else 0
    last_active_date = streak.last_active_date if streak else None

    # 2. Total XP (sum across all daily_activities)
    total_xp = (
        await db.execute(
            select(func.coalesce(func.sum(DailyActivity.xp_earned), 0)).where(
                DailyActivity.user_id == current_user.id
            )
        )
    ).scalar_one() or 0

    # 3. Distinct lessons ever completed (≥80% threshold, persisted)
    lessons_completed = (
        await db.execute(
            select(func.count(func.distinct(LessonAttempt.lesson_id))).where(
                LessonAttempt.user_id == current_user.id,
                LessonAttempt.is_completed.is_(True),
            )
        )
    ).scalar_one() or 0

    # 4. Top-level totals from exercise_attempts
    totals_row = (
        await db.execute(
            select(
                func.count().label("total"),
                func.coalesce(
                    func.sum(case((ExerciseAttempt.is_correct, 1), else_=0)), 0
                ).label("correct"),
            ).where(ExerciseAttempt.user_id == current_user.id)
        )
    ).one()
    total_exercise_attempts = totals_row.total or 0
    overall_correct = totals_row.correct or 0
    overall_winrate = (
        overall_correct / total_exercise_attempts
        if total_exercise_attempts
        else 0.0
    )

    # 5. Per-type aggregates
    type_rows = (
        await db.execute(
            select(
                ExerciseAttempt.exercise_type,
                func.count().label("total"),
                func.coalesce(
                    func.sum(case((ExerciseAttempt.is_correct, 1), else_=0)), 0
                ).label("correct"),
            )
            .where(ExerciseAttempt.user_id == current_user.id)
            .group_by(ExerciseAttempt.exercise_type)
            .order_by(ExerciseAttempt.exercise_type)
        )
    ).all()
    by_type = [
        TypeStats(
            exercise_type=row.exercise_type,
            total_attempts=row.total,
            correct_attempts=row.correct,
            winrate=(row.correct / row.total) if row.total else 0.0,
        )
        for row in type_rows
    ]

    # 6. Per-lesson aggregates from exercise_attempts
    lesson_attempt_rows = (
        await db.execute(
            select(
                ExerciseAttempt.lesson_id,
                ExerciseAttempt.section_id,
                func.count(func.distinct(ExerciseAttempt.exercise_id)).label(
                    "attempted"
                ),
                func.count().label("total"),
                func.coalesce(
                    func.sum(case((ExerciseAttempt.is_correct, 1), else_=0)), 0
                ).label("correct"),
            )
            .where(ExerciseAttempt.user_id == current_user.id)
            .group_by(ExerciseAttempt.lesson_id, ExerciseAttempt.section_id)
        )
    ).all()
    lesson_aggregates: dict[UUID, dict] = {
        row.lesson_id: {
            "section_id": row.section_id,
            "attempted": row.attempted,
            "total": row.total,
            "correct": row.correct,
        }
        for row in lesson_attempt_rows
    }

    # 7. Per-lesson best score (correct/total) and is_completed from lesson_attempts.
    # NULLIF guards against divide-by-zero for empty attempts.
    best_score_rows = (
        await db.execute(
            select(
                LessonAttempt.lesson_id,
                func.max(
                    LessonAttempt.correct_count
                    * 1.0
                    / func.nullif(LessonAttempt.total_count, 0)
                ).label("best"),
                func.bool_or(LessonAttempt.is_completed).label("any_completed"),
            )
            .where(LessonAttempt.user_id == current_user.id)
            .group_by(LessonAttempt.lesson_id)
        )
    ).all()
    lesson_best: dict[UUID, tuple[float, bool]] = {
        row.lesson_id: (float(row.best or 0.0), bool(row.any_completed))
        for row in best_score_rows
    }

    # 8. Course structure for the user — required so sections/lessons with
    # zero attempts still appear in the response (academic completeness:
    # the profile page should show the full roadmap, not just touched parts).
    course_id = current_user.course_id
    sections: list[SectionStats] = []
    if course_id is not None:
        course = (
            await db.execute(
                select(Course)
                .where(Course.id == course_id)
                .options(
                    selectinload(Course.sections)
                    .selectinload(Section.lessons)
                    .selectinload(Lesson.exercises)
                )
            )
        ).scalar_one_or_none()

        if course is not None:
            for section in course.sections:
                lesson_stats: list[LessonStats] = []
                section_attempted = 0
                section_total = 0
                section_correct = 0
                for lesson in section.lessons:
                    agg = lesson_aggregates.get(lesson.id)
                    best, any_completed = lesson_best.get(lesson.id, (0.0, False))
                    attempted = agg["attempted"] if agg else 0
                    total_attempts = agg["total"] if agg else 0
                    correct_attempts = agg["correct"] if agg else 0
                    section_attempted += attempted
                    section_total += total_attempts
                    section_correct += correct_attempts
                    lesson_stats.append(
                        LessonStats(
                            lesson_id=lesson.id,
                            lesson_title=lesson.title,
                            total_exercises=len(lesson.exercises),
                            attempted=attempted,
                            correct_attempts=correct_attempts,
                            total_attempts=total_attempts,
                            winrate=(
                                correct_attempts / total_attempts
                                if total_attempts
                                else 0.0
                            ),
                            is_completed=any_completed,
                            best_score=best,
                        )
                    )
                sections.append(
                    SectionStats(
                        section_id=section.id,
                        section_title=section.title,
                        total_exercises=sum(
                            len(lesson.exercises) for lesson in section.lessons
                        ),
                        attempted=section_attempted,
                        correct_attempts=section_correct,
                        total_attempts=section_total,
                        winrate=(
                            section_correct / section_total
                            if section_total
                            else 0.0
                        ),
                        lessons=lesson_stats,
                    )
                )

    return UserStats(
        total_xp=int(total_xp),
        current_streak=current_streak,
        longest_streak=longest_streak,
        lessons_completed=int(lessons_completed),
        total_exercise_attempts=total_exercise_attempts,
        overall_winrate=overall_winrate,
        sections=sections,
        by_type=by_type,
        last_active_date=last_active_date,
    )
