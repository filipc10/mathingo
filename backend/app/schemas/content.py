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


# ---------- Submission ----------


class AnswerSubmission(BaseModel):
    exercise_id: UUID
    # answer accepts the union of types the supported exercise types use:
    #   multiple_choice → int (option index)
    #   numeric         → int | float
    # The endpoint validates the type matches the exercise's exercise_type
    # at evaluation time.
    answer: int | float | str


class SubmissionRequest(BaseModel):
    answers: list[AnswerSubmission]


class ExerciseResult(BaseModel):
    exercise_id: UUID
    correct: bool
    user_answer: int | float | str
    correct_answer: int | float | str
    explanation: str | None


class ScoreSummary(BaseModel):
    correct_count: int
    total_count: int
    all_correct: bool


class SubmissionResponse(BaseModel):
    lesson_id: UUID
    results: list[ExerciseResult]
    score: ScoreSummary
