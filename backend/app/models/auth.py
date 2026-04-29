from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import TIMESTAMP, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base, IDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.content import Course
    from app.models.progress import (
        DailyActivity,
        LessonAttempt,
        Streak,
        UserLessonProgress,
    )


class User(IDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(320), unique=True, nullable=False, index=True
    )
    first_name: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    display_name: Mapped[str] = mapped_column(String(40), nullable=False)
    daily_xp_goal: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("20")
    )
    course_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("courses.id"),
        nullable=True,
        index=True,
    )

    course: Mapped["Course | None"] = relationship(back_populates="users")
    lesson_progress: Mapped[list["UserLessonProgress"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    lesson_attempts: Mapped[list["LessonAttempt"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    streak: Mapped["Streak | None"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    daily_activities: Mapped[list["DailyActivity"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class MagicLinkToken(IDMixin, Base):
    __tablename__ = "magic_link_tokens"

    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, index=True
    )
    consumed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
