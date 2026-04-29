from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StrictFloat, StrictInt


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
    # StrictInt / StrictFloat (vs. plain int / float) reject booleans at
    # parse time — Python's bool is a subclass of int, so a lax Union would
    # silently coerce true→1 and let it sail past a runtime isinstance check
    # in the evaluator. With Strict the user gets a Pydantic 422 instead.
    # `str` is kept for future exercise types (matching, step_ordering).
    answer: StrictInt | StrictFloat | str


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
    progress: "ProgressInfo"


class ProgressInfo(BaseModel):
    is_completed: bool       # this attempt scored ≥ 80%
    xp_earned: int           # awarded only on first completion
    user_streak: int         # current_length after this submit
    user_xp_today: int       # today's accumulated XP after this submit


class CourseProgressResponse(BaseModel):
    course_id: UUID
    completed_lesson_ids: list[UUID]


# ---------- Per-exercise check (stateless, no DB write) ----------


class ExerciseCheckRequest(BaseModel):
    answer: StrictInt | StrictFloat | str


class ExerciseCheckResponse(BaseModel):
    exercise_id: UUID
    correct: bool
    user_answer: int | float | str
    correct_answer: int | float | str
    explanation: str | None


# Resolve the forward-ref for SubmissionResponse.progress
SubmissionResponse.model_rebuild()
