from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, StrictBool, StrictFloat, StrictInt, StrictStr


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


# Mirrors AnswerSubmission.answer in app/schemas/content.py — the chat
# endpoint accepts whatever shape the user submitted to /check or /submit.
# StrictBool is listed first so a bool isn't silently coerced to int.
ChatAnswerValue = (
    StrictBool
    | StrictInt
    | StrictFloat
    | str
    | dict[StrictStr, StrictStr]
    | list[StrictStr]
)


class ExplainRequest(BaseModel):
    """Body for POST /exercises/{id}/explain.

    `user_answer` is what the student submitted (so the model can address
    why it's wrong); `messages` is the running conversation, with the
    final entry being the user's latest question. Capped server-side at
    `chat_session_message_limit`.
    """

    user_answer: ChatAnswerValue
    messages: list[ChatMessage] = Field(min_length=1)


class ChatUsageInfo(BaseModel):
    """Metadata returned via SSE before streaming starts.

    Lets the client show 'X / 20 dnes' without an extra round trip.
    """

    messages_used_today: int
    daily_limit: int


class ExerciseContextSummary(BaseModel):
    """Public-safe view of an exercise (no answer fields)."""

    id: UUID
    prompt: str
    exercise_type: str
    correct_answer: bool | int | float | str | dict[str, str] | list[str]
    user_answer: bool | int | float | str | dict[str, str] | list[str]
