from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.models import MagicLinkToken
from app.schemas.auth import SignInRequest, SignInResponse
from app.services.auth import generate_magic_link_token
from app.services.email import send_magic_link

router = APIRouter(tags=["auth"])


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
