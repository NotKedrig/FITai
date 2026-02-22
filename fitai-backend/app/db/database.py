from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.config import get_settings


settings = get_settings()

Base = declarative_base()


def _ensure_async_url(url: str) -> str:
    """Ensure DATABASE_URL uses postgresql+asyncpg for async engine."""
    if url.startswith("postgresql://") and "postgresql+asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def get_engine() -> AsyncEngine:
    url = _ensure_async_url(settings.DATABASE_URL)
    return create_async_engine(url, echo=False)


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

