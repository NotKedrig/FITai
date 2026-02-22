from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENVIRONMENT: str = "development"
    ALLOWED_ORIGINS: str = "*"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    DATABASE_URL: str
    REDIS_URL: Optional[str] = None
    SECRET_KEY: str

    # JWT settings
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    AI_PROVIDER: str = "gemini"

    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.0-flash"

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    OLLAMA_BASE_URL: Optional[str] = None
    OLLAMA_MODEL: str = "llama3.2:3b"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

