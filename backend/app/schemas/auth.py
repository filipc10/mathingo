from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# Display name shows up in the leaderboard and on the profile header,
# so it has to fit a single line, sort sensibly, and survive being
# typed back into a URL. ASCII letters + digits + `_ . -` covers the
# real cases (luki-mt, petra.vse, marie_bp) without opening the door
# to spaces, emoji, mid-word diacritics, or zero-width characters.
DISPLAY_NAME_PATTERN = r"^[A-Za-z0-9_.\-]+$"


class SignInRequest(BaseModel):
    email: EmailStr


class SignInResponse(BaseModel):
    status: str


class VerifyRequest(BaseModel):
    token: str = Field(min_length=1, max_length=128)


class VerifyResponse(BaseModel):
    redirect_to: str


class OnboardingRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    first_name: str = Field(min_length=1, max_length=40)
    display_name: str = Field(
        min_length=3, max_length=30, pattern=DISPLAY_NAME_PATTERN
    )
    daily_xp_goal: Literal[10, 20, 40]
    avatar_variant: Literal["marble", "beam", "pixel", "sunset", "ring", "bauhaus"]
    avatar_palette: Literal["blue", "green", "purple", "sunset", "mono"]


class OnboardingResponse(BaseModel):
    status: str


class MeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    first_name: str
    display_name: str
    daily_xp_goal: int
    avatar_variant: str
    avatar_palette: str
    streak: int
    xp_today: int
    last_activity_date: date | None
