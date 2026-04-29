"""Leaderboard endpoints — weekly and all-time XP rankings.

Ordering: xp DESC, current_streak DESC (tie-breaker), users.created_at ASC
(deterministic for ties on both XP and streak — earliest joiner wins).

We mount on /leaderboard (no /api prefix). Nginx proxies /api/* into
backend / so the browser hits /api/leaderboard/* and reaches us at
/leaderboard/*.
"""

from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.dependencies import get_current_user
from app.models import DailyActivity, Streak, User
from app.schemas.leaderboard import LeaderboardEntry, LeaderboardResponse

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


def _week_start_utc() -> date:
    """Monday 00:00 UTC of the current ISO week (Monday=0 in Python)."""
    today = datetime.now(UTC).date()
    return today - timedelta(days=today.weekday())


async def _build_leaderboard(
    *,
    db: AsyncSession,
    current_user: User,
    since: date | None,
) -> LeaderboardResponse:
    """Common path for /weekly and /total. `since=None` means all-time.

    Single ordered query, take first 10 in memory, then fall through the
    rest only if the current user wasn't in the top 10. For thesis-tier
    user counts (~50) this beats a separate window-function rank query
    in code clarity without measurable cost.
    """
    xp_subq = select(
        DailyActivity.user_id.label("user_id"),
        func.sum(DailyActivity.xp_earned).label("xp"),
    )
    if since is not None:
        xp_subq = xp_subq.where(DailyActivity.activity_date >= since)
    xp_subq = xp_subq.group_by(DailyActivity.user_id).subquery()

    stmt = (
        select(
            User.id,
            User.display_name,
            xp_subq.c.xp,
            Streak.current_length,
        )
        .join(xp_subq, xp_subq.c.user_id == User.id)
        .outerjoin(Streak, Streak.user_id == User.id)
        .where(User.display_name != "")
        .where(xp_subq.c.xp > 0)
        .order_by(
            desc(xp_subq.c.xp),
            desc(func.coalesce(Streak.current_length, 0)),
            User.created_at.asc(),
        )
    )
    rows = (await db.execute(stmt)).all()

    entries: list[LeaderboardEntry] = []
    user_rank: int | None = None
    user_xp: int | None = None

    for i, row in enumerate(rows[:10], start=1):
        is_me = row.id == current_user.id
        if is_me:
            user_rank = i
            user_xp = int(row.xp)
        entries.append(
            LeaderboardEntry(
                rank=i,
                user_id=row.id,
                display_name=row.display_name,
                xp=int(row.xp),
                streak=row.current_length or 0,
                is_current_user=is_me,
            )
        )

    if user_rank is None:
        for i, row in enumerate(rows, start=1):
            if row.id == current_user.id:
                user_rank = i
                user_xp = int(row.xp)
                break

    return LeaderboardResponse(
        entries=entries,
        user_rank=user_rank,
        user_xp=user_xp,
        total_users=len(rows),
    )


@router.get("/weekly", response_model=LeaderboardResponse)
async def get_weekly_leaderboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LeaderboardResponse:
    return await _build_leaderboard(
        db=db, current_user=current_user, since=_week_start_utc()
    )


@router.get("/total", response_model=LeaderboardResponse)
async def get_total_leaderboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LeaderboardResponse:
    return await _build_leaderboard(db=db, current_user=current_user, since=None)
