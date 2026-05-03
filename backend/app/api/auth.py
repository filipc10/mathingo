from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.dependencies import get_current_user
from app.models import Course, DailyActivity, MagicLinkToken, Streak, User
from app.schemas.auth import (
    MeResponse,
    OnboardingRequest,
    OnboardingResponse,
    SignInRequest,
    SignInResponse,
    VerifyRequest,
    VerifyResponse,
)
from app.services.auth import (
    create_session_jwt,
    generate_magic_link_token,
    hash_token,
)
from app.services.email import send_magic_link

router = APIRouter(tags=["auth"])

COOKIE_NAME = "mathingo_session"


def _set_session_cookie(response: Response, jwt_value: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=jwt_value,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        max_age=settings.jwt_expire_days * 24 * 3600,
        path="/",
    )


@router.post("/signin", response_model=SignInResponse)
async def signin(
    payload: SignInRequest,
    db: AsyncSession = Depends(get_db),
) -> SignInResponse:
    plain_token, token_hash = generate_magic_link_token()
    expires_at = datetime.now(UTC) + timedelta(
        minutes=settings.magic_link_expire_minutes
    )

    db.add(
        MagicLinkToken(
            email=payload.email,
            token_hash=token_hash,
            expires_at=expires_at,
        )
    )
    await db.commit()

    await send_magic_link(payload.email, plain_token)

    return SignInResponse(status="sent")


@router.get("/click")
async def click(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Idempotent magic-link landing.

    Looks up the token by hash but never marks it consumed. Enterprise email
    gateways (e.g. Microsoft Defender for VŠE inboxes) prefetch URLs in
    incoming mail for malware scanning; if the GET endpoint consumed the
    token, the gateway would burn it before the human ever clicked. Token
    consumption happens only in POST /auth/verify, triggered by an explicit
    user action on the /click page.
    """
    digest = hash_token(token)
    result = await db.execute(
        select(MagicLinkToken).where(MagicLinkToken.token_hash == digest)
    )
    record = result.scalar_one_or_none()

    if record is None:
        return RedirectResponse(url="/signin?error=invalid", status_code=302)
    if record.consumed_at is not None:
        return RedirectResponse(url="/signin?error=already_used", status_code=302)
    if record.expires_at < datetime.now(UTC):
        return RedirectResponse(url="/signin?error=expired", status_code=302)

    return RedirectResponse(url=f"/click?token={token}", status_code=302)


@router.post("/verify", response_model=VerifyResponse)
async def verify(
    payload: VerifyRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> VerifyResponse:
    """Consume a magic-link token, create the session cookie, return redirect.

    Side-effecting on purpose — see the docstring on /auth/click for why GET
    is split from POST.
    """
    digest = hash_token(payload.token)
    result = await db.execute(
        select(MagicLinkToken).where(MagicLinkToken.token_hash == digest)
    )
    record = result.scalar_one_or_none()

    now = datetime.now(UTC)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="invalid")
    if record.consumed_at is not None:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="already_used")
    if record.expires_at < now:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="expired")

    record.consumed_at = now

    user_result = await db.execute(select(User).where(User.email == record.email))
    user = user_result.scalar_one_or_none()
    if user is None:
        course_result = await db.execute(
            select(Course).where(Course.code == "4MM101")
        )
        course = course_result.scalar_one_or_none()
        user = User(
            email=record.email,
            first_name="",
            display_name="",
            daily_xp_goal=20,
            avatar_variant="beam",
            avatar_palette="blue",
            course_id=course.id if course is not None else None,
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)

    needs_onboarding = user.first_name == "" or user.display_name == ""
    redirect_to = "/onboarding" if needs_onboarding else "/learn"
    _set_session_cookie(response, create_session_jwt(user.id))
    return VerifyResponse(redirect_to=redirect_to)


@router.post("/onboarding", response_model=OnboardingResponse)
async def onboarding(
    payload: OnboardingRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OnboardingResponse:
    collision = await db.execute(
        select(User).where(
            User.display_name == payload.display_name,
            User.id != user.id,
        )
    )
    if collision.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="display_name_taken",
        )

    user.first_name = payload.first_name
    user.display_name = payload.display_name
    user.daily_xp_goal = payload.daily_xp_goal
    user.avatar_variant = payload.avatar_variant
    user.avatar_palette = payload.avatar_palette
    await db.commit()

    return OnboardingResponse(status="ok")


@router.get("/me", response_model=MeResponse)
async def me(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MeResponse:
    streak = (
        await db.execute(select(Streak).where(Streak.user_id == user.id))
    ).scalar_one_or_none()

    today = datetime.now(UTC).date()
    xp_today_row = await db.execute(
        select(DailyActivity.xp_earned).where(
            DailyActivity.user_id == user.id,
            DailyActivity.activity_date == today,
        )
    )
    xp_today = xp_today_row.scalar_one_or_none() or 0

    return MeResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        display_name=user.display_name,
        daily_xp_goal=user.daily_xp_goal,
        avatar_variant=user.avatar_variant,
        avatar_palette=user.avatar_palette,
        streak=streak.current_length if streak else 0,
        xp_today=xp_today,
        last_activity_date=streak.last_active_date if streak else None,
    )


@router.post("/signout")
async def signout(response: Response) -> dict[str, str]:
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"status": "ok"}
