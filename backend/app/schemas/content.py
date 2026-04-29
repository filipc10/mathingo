from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    title: str
    description: str | None


class LessonSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_index: int
    title: str
    description: str | None
    xp_reward: int


class SectionWithLessons(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_index: int
    title: str
    description: str | None
    lessons: list[LessonSummary]


class CourseStructure(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    title: str
    sections: list[SectionWithLessons]


class ExerciseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_index: int
    exercise_type: str
    prompt: str
    explanation: str | None
    difficulty: int
    payload: dict[str, Any]


class LessonDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_index: int
    title: str
    description: str | None
    xp_reward: int
    exercises: list[ExerciseResponse]
