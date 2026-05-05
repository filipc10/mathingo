"""AI explanation chat for incorrect exercise answers.

Streaming endpoint that calls the Anthropic Claude API. Each user message
counts toward two caps:
  - chat_session_message_limit  (per chat instance, enforced by the client
    *and* re-checked here against the request payload — `messages` cannot
    contain more than the cap of user turns)
  - chat_daily_message_limit    (per user per UTC day, enforced atomically
    by upserting chat_usage with ON CONFLICT … DO UPDATE … RETURNING)

The model is `settings.anthropic_model` (default claude-sonnet-4-6). No
extended thinking — pedagogical replies are short (3–4 sentences), so
adaptive thinking would just inflate cost. We pass `effort: "low"` to
keep responses terse.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import AsyncIterator
from uuid import UUID

from anthropic import AsyncAnthropic, APIError
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.content import _evaluate
from app.config import settings
from app.db import get_db
from app.dependencies import get_current_user
from app.models import ChatUsage, Exercise, User
from app.schemas.chat import ExplainRequest

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


SYSTEM_PROMPT = """\
Jsi přátelský a trpělivý učitel matematiky pro studenty Vysoké školy ekonomické v Praze.
Pomáháš studentovi pochopit, proč jeho odpověď na cvičení nebyla správná, a vysvětluješ
mu látku tak, aby si ji zapamatoval.

Pravidla:
- Odpovídej česky.
- Buď stručný/á: maximálně 3–4 věty na odpověď.
- Když potřebuješ matematickou notaci, používej LaTeX: $...$ pro inline a $$...$$ pro
  blokový vzorec.
- Neprozrazuj odpověď přímo, dokud se na ni student výslovně nezeptá. Naváděj ho otázkami
  a postupnými kroky.
- Vyhýbej se obecným frázím („dobrá otázka", „výborně"). Jdi rovnou k věci.
- Pokud student položí otázku, která nesouvisí s daným cvičením ani s matematikou,
  zdvořile ho odkaž zpět ke cvičení.\
"""


def _format_answer(
    exercise: Exercise, value: object
) -> str:
    """Render an answer in a form the LLM can reason about.

    The wire format for each type is terse — just an index, a bool, or
    a list of step ids. Without resolving these to the underlying text,
    the model would have nothing concrete to reason about.
    """
    if exercise.exercise_type == "multiple_choice" and isinstance(value, int):
        options = exercise.payload.get("options") or []
        if 0 <= value < len(options):
            return f"{options[value]!r} (index {value})"

    if exercise.exercise_type == "true_false" and isinstance(value, bool):
        return "Pravda" if value else "Nepravda"

    if exercise.exercise_type == "matching" and isinstance(value, dict):
        if not value:
            return "(žádné přiřazení)"
        lines = [f"  - {item} → {cat}" for item, cat in value.items()]
        return "\n" + "\n".join(lines)

    if exercise.exercise_type == "step_ordering" and isinstance(value, list):
        steps_by_id = {
            s["id"]: s["text"]
            for s in (exercise.payload.get("steps") or [])
            if isinstance(s, dict)
        }
        lines = [
            f"  {i + 1}. {steps_by_id.get(sid, sid)}"
            for i, sid in enumerate(value)
        ]
        return "\n" + "\n".join(lines) if lines else "(žádné pořadí)"

    return str(value)


def _exercise_context_text(
    *, exercise: Exercise, user_answer: object, correct_answer: object
) -> str:
    """Render the exercise + the student's wrong answer as the first user
    message. Keeps the system prompt static so prompt-cache prefix stays
    stable across users (even if the cache minimum is far above what we
    send today, leaving the option open is cheap)."""
    parts = [
        f"Cvičení (typ: {exercise.exercise_type}):\n{exercise.prompt}",
    ]
    if exercise.exercise_type == "multiple_choice":
        options = exercise.payload.get("options") or []
        rendered_options = "\n".join(
            f"  {i}. {opt}" for i, opt in enumerate(options)
        )
        parts.append(f"Nabízené možnosti:\n{rendered_options}")
    elif exercise.exercise_type == "matching":
        items = exercise.payload.get("items") or []
        categories = exercise.payload.get("categories") or []
        parts.append(
            "Položky k přiřazení:\n"
            + "\n".join(f"  - {item}" for item in items)
            + "\n\nKategorie:\n"
            + "\n".join(f"  - {cat}" for cat in categories)
        )
    elif exercise.exercise_type == "step_ordering":
        steps = exercise.payload.get("steps") or []
        parts.append(
            "Kroky (v zamíchaném pořadí — student je řadí):\n"
            + "\n".join(
                f"  - {s['id']}: {s['text']}"
                for s in steps
                if isinstance(s, dict)
            )
        )
    parts.append(
        f"Moje odpověď: {_format_answer(exercise, user_answer)}\n"
        f"Správná odpověď: {_format_answer(exercise, correct_answer)}"
    )
    parts.append("Pomoz mi pochopit, proč jsem to měl/a špatně.")
    return "\n\n".join(parts)


async def _bump_chat_usage(
    *, db: AsyncSession, user_id: UUID
) -> int:
    """Atomically increment today's message count for the user and return
    the new total. Race-safe via ON CONFLICT … DO UPDATE … RETURNING."""
    today = datetime.now(UTC).date()
    stmt = (
        pg_insert(ChatUsage)
        .values(user_id=user_id, usage_date=today, message_count=1)
        .on_conflict_do_update(
            constraint="uq_chat_usage_user_date",
            set_={"message_count": ChatUsage.message_count + 1},
        )
        .returning(ChatUsage.message_count)
    )
    result = await db.execute(stmt)
    new_count = result.scalar_one()
    await db.commit()
    return new_count


@router.post("/exercises/{exercise_id}/explain")
async def explain_exercise(
    exercise_id: UUID,
    request: ExplainRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ai_chat_not_configured",
        )

    # Per-session cap: count the number of user turns in the supplied
    # history. The frontend enforces this too, but we re-check so a
    # crafted request can't bypass it.
    user_turns = sum(1 for m in request.messages if m.role == "user")
    if user_turns > settings.chat_session_message_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="session_message_limit_reached",
        )

    exercise = (
        await db.execute(select(Exercise).where(Exercise.id == exercise_id))
    ).scalar_one_or_none()
    if exercise is None:
        raise HTTPException(status_code=404, detail="exercise_not_found")

    # Re-evaluate to recover correct_answer (and to defend against a
    # client claiming the answer was wrong when it wasn't).
    is_correct, correct_answer = _evaluate(exercise, request.user_answer)
    if is_correct:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="answer_was_correct_no_explanation_needed",
        )

    # Atomic UPSERT: enforce daily cap + return new count for the SSE meta.
    new_count = await _bump_chat_usage(db=db, user_id=current_user.id)
    if new_count > settings.chat_daily_message_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="daily_message_limit_reached",
        )

    # Build the message list. The first user turn always contains the
    # exercise context so the model has something concrete to ground on
    # even if the frontend forgets to repeat it. Subsequent turns are the
    # student's questions plus prior assistant replies (preserved in the
    # request body — the client owns the history).
    context = _exercise_context_text(
        exercise=exercise,
        user_answer=request.user_answer,
        correct_answer=correct_answer,
    )
    api_messages: list[dict] = [{"role": "user", "content": context}]
    for m in request.messages:
        api_messages.append({"role": m.role, "content": m.content})

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def event_stream() -> AsyncIterator[bytes]:
        # First event: usage metadata so the client can update its
        # 'X / 20 dnes' counter immediately.
        meta = {
            "messages_used_today": new_count,
            "daily_limit": settings.chat_daily_message_limit,
        }
        yield f"event: usage\ndata: {json.dumps(meta)}\n\n".encode()

        try:
            async with client.messages.stream(
                model=settings.anthropic_model,
                max_tokens=600,
                system=SYSTEM_PROMPT,
                messages=api_messages,
            ) as stream:
                async for chunk in stream.text_stream:
                    payload = json.dumps({"text": chunk})
                    yield f"event: token\ndata: {payload}\n\n".encode()
        except APIError as e:
            logger.exception("anthropic_api_error", extra={"user": str(current_user.id)})
            err = {"detail": "ai_provider_error", "code": getattr(e, "status_code", None)}
            yield f"event: error\ndata: {json.dumps(err)}\n\n".encode()
            return
        except Exception:
            logger.exception("chat_stream_unexpected", extra={"user": str(current_user.id)})
            yield b"event: error\ndata: {\"detail\": \"internal_error\"}\n\n"
            return

        yield b"event: done\ndata: {}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx response buffering
        },
    )
