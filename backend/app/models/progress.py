from datetime import date, datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Integer,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base, IDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.auth import User
    from app.models.content import Exercise, Lesson


class LessonProgressStatus(StrEnum):
    LOCKED = "locked"
    AVAILABLE = "available"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class UserLessonProgress(IDMixin, TimestampMixin, Base):
    __tablename__ = "user_lesson_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", name="uq_ulp_user_lesson"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    lesson_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[LessonProgressStatus] = mapped_column(
        Enum(
            LessonProgressStatus,
            name="user_lesson_progress_status",
            native_enum=False,
            length=20,
            validate_strings=True,
        ),
        nullable=False,
        server_default=text("'locked'"),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship(back_populates="lesson_progress")
    lesson: Mapped["Lesson"] = relationship(back_populates="progress")


class LessonAttempt(IDMixin, Base):
    __tablename__ = "lesson_attempts"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lesson_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    xp_earned: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    correct_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    total_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="lesson_attempts")
    lesson: Mapped["Lesson"] = relationship(back_populates="attempts")
    exercise_attempts: Mapped[list["ExerciseAttempt"]] = relationship(
        back_populates="lesson_attempt",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ExerciseAttempt(IDMixin, Base):
    __tablename__ = "exercise_attempts"

    lesson_attempt_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("lesson_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exercise_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("exercises.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    answer: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    time_spent_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    lesson_attempt: Mapped["LessonAttempt"] = relationship(
        back_populates="exercise_attempts"
    )
    exercise: Mapped["Exercise"] = relationship(back_populates="attempts")


class Streak(IDMixin, TimestampMixin, Base):
    __tablename__ = "streaks"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    current_length: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    longest_length: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    last_active_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    user: Mapped["User"] = relationship(back_populates="streak")


class DailyActivity(IDMixin, Base):
    __tablename__ = "daily_activities"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "activity_date", name="uq_daily_activities_user_date"
        ),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    activity_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    xp_earned: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    lessons_completed: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="daily_activities")
