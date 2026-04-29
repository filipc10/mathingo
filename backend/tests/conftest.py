"""Test scaffolding shared across test modules.

The tests run inside the backend container against the live dev Postgres.
Each test inserts its own data under a unique email, exercises the endpoint
through httpx + ASGITransport, then cleans up via the same transaction.
This avoids needing a separate test database while keeping isolation
explicit (no fixtures with magic teardown).
"""

import os
import sys
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# DATABASE_URL is required to import app.config; tests run inside a container
# where it is already set via docker compose env, but be defensive.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://localhost/test")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("BACKEND_CORS_ORIGINS", "")
os.environ.setdefault("RESEND_API_KEY", "test")
os.environ.setdefault("APP_URL", "http://test")
os.environ.setdefault("ANTHROPIC_API_KEY", "test")

from app import db as app_db  # noqa: E402
from app.dependencies import get_current_user  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Course, User  # noqa: E402
from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402


@pytest_asyncio.fixture
async def db_session():
    """Fresh engine + session per test.

    The app-level engine was bound to whichever event loop first imported
    `app.db`; pytest-asyncio runs each test in its own loop, so reusing
    that engine raises 'Event loop is closed' during connection teardown.
    A per-test engine sidesteps the loop binding entirely. We also
    monkey-patch `app.db.AsyncSessionLocal` for the duration of the test
    so endpoints that go through `get_db` use the same engine.
    """
    from app.config import settings

    engine = create_async_engine(settings.database_url, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    original_factory = app_db.AsyncSessionLocal
    app_db.AsyncSessionLocal = session_factory
    try:
        async with session_factory() as session:
            yield session
    finally:
        app_db.AsyncSessionLocal = original_factory
        await engine.dispose()


@pytest_asyncio.fixture
async def test_user(db_session):
    """Create a transient user bound to the 4MM101 course and yield it.

    Cleanup deletes the user; CASCADE handles streaks / daily_activities /
    lesson_attempts / exercise_attempts.
    """
    course = (
        await db_session.execute(select(Course).where(Course.code == "4MM101"))
    ).scalar_one_or_none()

    user = User(
        email=f"test-{uuid4().hex}@mathingo.local",
        first_name="Test",
        display_name=f"test-{uuid4().hex[:8]}",
        daily_xp_goal=20,
        avatar_variant="beam",
        avatar_palette="blue",
        course_id=course.id if course else None,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    try:
        yield user
    finally:
        await db_session.delete(user)
        await db_session.commit()


@pytest_asyncio.fixture
async def client(test_user):
    """AsyncClient with get_current_user pinned to the fixture user."""
    app.dependency_overrides[get_current_user] = lambda: test_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
