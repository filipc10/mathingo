from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StrictBool, StrictFloat, StrictInt, StrictStr


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
    #   true_false      → bool
    #   cloze           → str
    #   matching        → dict[str, str]    (item → category)
    #   step_ordering   → list[str]         (step ids in order)
    # StrictBool is listed first — Python's bool is a subclass of int, so a
    # lax Union would coerce true→1 and let it sail past the evaluator's
    # isinstance checks. StrictBool / StrictInt / StrictFloat reject the
    # cross-type at parse time and return 422.
    answer: (
        StrictBool
        | StrictInt
        | StrictFloat
        | str
        | dict[StrictStr, StrictStr]
        | list[StrictStr]
    )


class SubmissionRequest(BaseModel):
    answers: list[AnswerSubmission]


AnswerValue = bool | int | float | str | dict[str, str] | list[str]


class ExerciseResult(BaseModel):
    exercise_id: UUID
    correct: bool
    user_answer: AnswerValue
    correct_answer: AnswerValue
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
    is_completed: bool       # this attempt scored ≥ 66%
    xp_earned: int           # awarded only on first completion
    user_streak: int         # current_length after this submit
    user_xp_today: int       # today's accumulated XP after this submit


class CourseProgressResponse(BaseModel):
    course_id: UUID
    completed_lesson_ids: list[UUID]


# ---------- Per-exercise check (stateless, no DB write) ----------


class ExerciseCheckRequest(BaseModel):
    answer: (
        StrictBool
        | StrictInt
        | StrictFloat
        | str
        | dict[StrictStr, StrictStr]
        | list[StrictStr]
    )


class ExerciseCheckResponse(BaseModel):
    exercise_id: UUID
    correct: bool
    user_answer: AnswerValue
    correct_answer: AnswerValue
    explanation: str | None


# Resolve the forward-ref for SubmissionResponse.progress
SubmissionResponse.model_rebuild()
