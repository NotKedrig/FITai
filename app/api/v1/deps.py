from collections.abc import AsyncIterator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session


async def get_db(  # type: ignore[override]
    session: AsyncSession = Depends(get_db_session),
) -> AsyncIterator[AsyncSession]:
    yield session

