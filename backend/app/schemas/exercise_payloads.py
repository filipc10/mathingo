"""Typed Pydantic models for exercise.payload JSONB content.

Storage stays a single `payload` JSONB column on `exercises` — the
"data" the renderer needs and the "correct answer" the evaluator
needs are both fields on the same object (matching the existing
multiple_choice / numeric pattern). These models are used by tests
to keep payload shapes honest, and by future seed scripts as
runtime validators.
"""

from pydantic import BaseModel, StrictBool, StrictStr


class ClozePayload(BaseModel):
    placeholder: str | None = None
    value: StrictStr
    alternates: list[StrictStr] = []
    case_sensitive: bool = False
    trim_whitespace: bool = True


class TrueFalsePayload(BaseModel):
    value: StrictBool


class MatchingPayload(BaseModel):
    items: list[StrictStr]
    categories: list[StrictStr]
    instructions: str | None = None
    assignments: dict[StrictStr, StrictStr]


class StepItem(BaseModel):
    id: StrictStr
    text: StrictStr


class StepOrderingPayload(BaseModel):
    steps: list[StepItem]
    instructions: str | None = None
    order: list[StrictStr]
