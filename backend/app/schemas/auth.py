from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SignInRequest(BaseModel):
    email: EmailStr


class SignInResponse(BaseModel):
    status: str


class OnboardingRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    first_name: str = Field(min_length=1, max_length=40)
    display_name: str = Field(min_length=3, max_length=30)
    daily_xp_goal: Literal[10, 20, 40]


class OnboardingResponse(BaseModel):
    status: str


class MeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    first_name: str
    display_name: str
    daily_xp_goal: int
