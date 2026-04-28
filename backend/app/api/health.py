from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)) -> JSONResponse:
    try:
        await db.execute(text("SELECT 1"))
        db_status = "ok"
        http_status = status.HTTP_200_OK
    except Exception:
        db_status = "error"
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        content={"app": "ok", "db": db_status},
        status_code=http_status,
    )
