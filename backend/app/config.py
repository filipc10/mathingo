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


settings = Settings()
