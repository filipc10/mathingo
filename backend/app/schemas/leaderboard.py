from uuid import UUID

from pydantic import BaseModel


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: UUID
    display_name: str
    xp: int
    streak: int
    is_current_user: bool


class LeaderboardResponse(BaseModel):
    """Top 10 entries plus the current user's rank when they're outside it.

    `user_rank` and `user_xp` are non-null whenever the user has any XP
    in the period (and thus appears in the underlying ordered list).
    Both stay null if the user hasn't earned XP in the period — the
    frontend then hides the 'Tvoje pozice' box.
    """

    entries: list[LeaderboardEntry]
    user_rank: int | None
    user_xp: int | None
    total_users: int
