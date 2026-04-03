from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Database
    DATABASE_URL: str = "postgresql://papernosh:papernosh@localhost:5432/papernosh"

    # JWT
    SECRET_KEY: str = "changeme-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"

    # SMTP
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@papernosh.io"

    # AI
    OPENAI_API_KEY: str = ""

    # Source limits
    ARXIV_MAX_RESULTS: int = 100
    OPENALEX_MAX_RESULTS: int = 100
    CROSSREF_MAX_RESULTS: int = 100

    # Runtime
    ENVIRONMENT: str = "development"


settings = Settings()
