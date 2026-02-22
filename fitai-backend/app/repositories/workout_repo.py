from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workout import Workout
from app.repositories.base import BaseRepository


class WorkoutRepository(BaseRepository[Workout]):
    """Repository for Workout model with additional query methods."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Workout)

    async def get_user_workouts(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[Workout]:
        """
        Get all workouts for a specific user with pagination.

        Args:
            user_id: User UUID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of workout instances ordered by started_at DESC
        """
        stmt = (
            select(Workout)
            .where(Workout.user_id == user_id)
            .order_by(Workout.started_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_workout(self, user_id: UUID) -> Workout | None:
        """
        Get the active workout for a user (where ended_at IS NULL).

        Args:
            user_id: User UUID

        Returns:
            Active workout instance or None if not found
        """
        stmt = select(Workout).where(
            Workout.user_id == user_id, Workout.ended_at.is_(None)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_many_by_id(self, ids: list[UUID]) -> list[Workout]:
        """
        Get workouts by a list of IDs. Order of results is not guaranteed.

        Args:
            ids: List of workout UUIDs

        Returns:
            List of workout instances
        """
        if not ids:
            return []
        stmt = select(Workout).where(Workout.id.in_(ids))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
