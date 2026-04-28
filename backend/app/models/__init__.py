from app.models.auth import MagicLinkToken, User
from app.models.base import Base, IDMixin, TimestampMixin

__all__ = [
    "Base",
    "IDMixin",
    "TimestampMixin",
    "User",
    "MagicLinkToken",
]
