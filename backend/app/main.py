import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, chat, content, health, leaderboard, push, users
from app.config import settings
from app.services.notification_scheduler import schedule_daily_jobs

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: register cron jobs and start the scheduler. AsyncIOScheduler
    # runs in the FastAPI event loop, so the daily slot callbacks share the
    # same async DB session machinery as request handlers.
    scheduler = AsyncIOScheduler(timezone="UTC")
    schedule_daily_jobs(scheduler)
    scheduler.start()
    app.state.scheduler = scheduler
    logger.info("notification scheduler started")

    try:
        yield
    finally:
        scheduler.shutdown(wait=True)
        logger.info("notification scheduler shut down")


app = FastAPI(title="Mathingo API", version="0.1.0", lifespan=lifespan)

origins = [s.strip() for s in settings.backend_cors_origins.split(",") if s.strip()]
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(health.router)
app.include_router(auth.router, prefix="/auth")
app.include_router(content.router)
app.include_router(chat.router)
app.include_router(leaderboard.router)
app.include_router(push.router)
app.include_router(users.router)
