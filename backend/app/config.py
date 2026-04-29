from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    database_url: str
    secret_key: str
    backend_cors_origins: str = ""

    # Resend (transactional email)
    resend_api_key: str

    # JWT session
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_days: int = 30

    # Magic link
    magic_link_expire_minutes: int = 15

    # Public application URL — used in magic link emails as the base for /auth/verify
    app_url: str = "https://mathingo.cz"

    # Anthropic Claude API — used by the per-exercise AI explanation chat.
    # User specified `claude-sonnet-4-7` which doesn't exist; using the latest
    # Sonnet (4.6). Override via env var to swap models without code changes.
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    chat_daily_message_limit: int = 20
    chat_session_message_limit: int = 5


settings = Settings()
