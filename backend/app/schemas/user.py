from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.auth import DISPLAY_NAME_PATTERN


class LessonStats(BaseModel):
    lesson_id: UUID
    lesson_title: str
    total_exercises: int
    attempted: int
    correct_attempts: int
    total_attempts: int
    winrate: float
    is_completed: bool
    best_score: float


class SectionStats(BaseModel):
    section_id: UUID
    section_title: str
    total_exercises: int
    attempted: int
    correct_attempts: int
    total_attempts: int
    winrate: float
    lessons: list[LessonStats]


class TypeStats(BaseModel):
    exercise_type: str
    total_attempts: int
    correct_attempts: int
    winrate: float


class UserStats(BaseModel):
    total_xp: int
    current_streak: int
    longest_streak: int
    lessons_completed: int
    total_exercise_attempts: int
    overall_winrate: float

    sections: list[SectionStats]
    by_type: list[TypeStats]

    last_active_date: date | None


class UserUpdateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    display_name: str | None = Field(
        default=None, min_length=3, max_length=30, pattern=DISPLAY_NAME_PATTERN
    )
    avatar_variant: (
        Literal["marble", "beam", "pixel", "sunset", "ring", "bauhaus"] | None
    ) = None
    avatar_palette: (
        Literal["blue", "green", "purple", "sunset", "mono"] | None
    ) = None


class UserUpdateResponse(BaseModel):
    status: str


SlotLiteral = Literal["morning", "noon", "evening"]


class NotificationPreferencesResponse(BaseModel):
    enabled: bool
    time_slot: SlotLiteral
    has_push_subscription: bool


class NotificationPreferencesUpdate(BaseModel):
    enabled: bool | None = None
    time_slot: SlotLiteral | None = None
