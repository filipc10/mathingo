from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, StrictFloat, StrictInt


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ExplainRequest(BaseModel):
    """Body for POST /exercises/{id}/explain.

    `user_answer` is what the student submitted (so the model can address
    why it's wrong); `messages` is the running conversation, with the
    final entry being the user's latest question. Capped server-side at
    `chat_session_message_limit`.
    """

    user_answer: StrictInt | StrictFloat | str
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
    correct_answer: int | float | str
    user_answer: int | float | str
