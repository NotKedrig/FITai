from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exercise import Exercise
from app.repositories.base import BaseRepository


class ExerciseRepository(BaseRepository[Exercise]):
    """Repository for Exercise model with additional query methods."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Exercise)

    async def get_global_exercises(self) -> list[Exercise]:
        """
        Get all global exercises (where is_global = True).

        Returns:
            List of global exercise instances ordered by name
        """
        stmt = (
            select(Exercise)
            .where(Exercise.is_global == True)  # noqa: E712
            .order_by(Exercise.name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search_exercises(self, query: str) -> list[Exercise]:
        """
        Search exercises by name (case-insensitive).

        Args:
            query: Search query string

        Returns:
            List of matching exercise instances ordered by name
        """
        stmt = (
            select(Exercise)
            .where(Exercise.name.ilike(f"%{query}%"))
            .order_by(Exercise.name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_global_exercises_with_search(
        self, search: str | None = None
    ) -> list[Exercise]:
        """
        Get global exercises, optionally filtered by name search.

        Args:
            search: Optional search string for name (case-insensitive)

        Returns:
            List of global exercise instances ordered by name
        """
        stmt = select(Exercise).where(Exercise.is_global == True)  # noqa: E712
        if search:
            stmt = stmt.where(Exercise.name.ilike(f"%{search}%"))
        stmt = stmt.order_by(Exercise.name)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
