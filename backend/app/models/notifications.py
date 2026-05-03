from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base, IDMixin

if TYPE_CHECKING:
    from app.models.auth import User


class NotificationPreferences(IDMixin, Base):
    """Per-user notification settings.

    Default `enabled=False` is the opt-in promise: a fresh row never
    sends push without the user explicitly flipping it on. `time_slot`
    is one of morning/noon/evening — the CHECK constraint guards
    against typos at INSERT time. `daily_max` exists as a column so
    a future feature can lift it, but the current scheduler hard-codes
    one notification per day per slot.
    """

    __tablename__ = "notification_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_notification_preferences_user"),
        CheckConstraint(
            "time_slot IN ('morning', 'noon', 'evening')",
            name="ck_notification_preferences_time_slot",
        ),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    time_slot: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'morning'")
    )
    daily_max: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="notification_preferences")


class NotificationLog(IDMixin, Base):
    """One row per delivered (or attempted) push.

    UNIQUE (user_id, sent_date, time_slot) is the single source of truth
    for "we already pushed this user today" — INSERT before send means a
    second cron run gets IntegrityError and exits cleanly without
    reaching pywebpush. `text_used` stores the raw template (not the
    rendered string) so the anti-repetition pool keys on the same value
    that picker.choose() sees.
    """

    __tablename__ = "notification_logs"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "sent_date",
            "time_slot",
            name="uq_notification_logs_user_date_slot",
        ),
        Index("ix_notification_logs_user_date", "user_id", "sent_date"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    sent_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    sent_date: Mapped[date] = mapped_column(Date, nullable=False)
    time_slot: Mapped[str] = mapped_column(String(20), nullable=False)
    text_used: Mapped[str] = mapped_column(Text, nullable=False)
    push_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'pending'")
    )

    user: Mapped["User"] = relationship(back_populates="notification_logs")
