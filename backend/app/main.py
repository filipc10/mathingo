from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, chat, content, health, leaderboard, push, users
from app.config import settings

app = FastAPI(title="Mathingo API", version="0.1.0")

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
