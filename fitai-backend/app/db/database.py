from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.config import get_settings


settings = get_settings()

Base = declarative_base()


def _ensure_async_url(url: str) -> str:
    """Ensure DATABASE_URL uses postgresql+asyncpg for async engine.
    Handles postgres:// (Railway/default) and postgresql://."""
    if "postgresql+asyncpg" in url:
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url[11:]  # postgres:// -> postgresql+asyncpg://
    return url


def get_engine() -> AsyncEngine:
    url = _ensure_async_url(settings.DATABASE_URL)
    return create_async_engine(
        url,
        echo=False,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_pre_ping=True,
    )


engine: AsyncEngine = get_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncIterator[AsyncSession]:
    """Async DB session generator for dependency injection."""
    async with AsyncSessionLocal() as session:
        yield session

