from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.config import get_settings


settings = get_settings()

Base = declarative_base()


def get_engine() -> AsyncEngine:
    return create_async_engine(settings.DATABASE_URL, echo=False)


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

