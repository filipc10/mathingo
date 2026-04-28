from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.auth import User
    from app.models.progress import ExerciseAttempt, LessonAttempt, UserLessonProgress


class ExerciseType(StrEnum):
    MULTIPLE_CHOICE = "multiple_choice"
    NUMERIC = "numeric"
    TRUE_FALSE = "true_false"
    MATCHING = "matching"
    STEP_ORDERING = "step_ordering"


class Course(IDMixin, TimestampMixin, Base):
    __tablename__ = "courses"

    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    sections: Mapped[list["Section"]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Section.order_index",
    )
    users: Mapped[list["User"]] = relationship(back_populates="course")


class Section(IDMixin, TimestampMixin, Base):
    __tablename__ = "sections"
    __table_args__ = (
        UniqueConstraint("course_id", "order_index", name="uq_sections_course_order"),
    )

    course_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    course: Mapped["Course"] = relationship(back_populates="sections")
    lessons: Mapped[list["Lesson"]] = relationship(
        back_populates="section",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Lesson.order_index",
    )


class Lesson(IDMixin, TimestampMixin, Base):
    __tablename__ = "lessons"
    __table_args__ = (
        UniqueConstraint("section_id", "order_index", name="uq_lessons_section_order"),
    )

    section_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sections.id", ondelete="CASCADE"),
        nullable=False,
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    xp_reward: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("10")
    )

    section: Mapped["Section"] = relationship(back_populates="lessons")
    exercises: Mapped[list["Exercise"]] = relationship(
        back_populates="lesson",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Exercise.order_index",
    )
    progress: Mapped[list["UserLessonProgress"]] = relationship(
        back_populates="lesson",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    attempts: Mapped[list["LessonAttempt"]] = relationship(
        back_populates="lesson",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Exercise(IDMixin, TimestampMixin, Base):
    __tablename__ = "exercises"
    __table_args__ = (
        UniqueConstraint("lesson_id", "order_index", name="uq_exercises_lesson_order"),
        CheckConstraint(
            "difficulty BETWEEN 1 AND 5", name="ck_exercises_difficulty_range"
        ),
    )

    lesson_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    exercise_type: Mapped[ExerciseType] = mapped_column(
        Enum(
            ExerciseType,
            name="exercise_type",
            native_enum=False,
            length=20,
            validate_strings=True,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    payload: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )

    lesson: Mapped["Lesson"] = relationship(back_populates="exercises")
    attempts: Mapped[list["ExerciseAttempt"]] = relationship(
        back_populates="exercise",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
