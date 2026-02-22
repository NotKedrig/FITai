from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.set import Set
from app.repositories.base import BaseRepository


class SetRepository(BaseRepository[Set]):
    """Repository for Set model with additional query methods."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Set)

    async def get_sets_for_workout(self, workout_id: UUID) -> list[Set]:
        """
        Get all sets for a specific workout.

        Args:
            workout_id: Workout UUID

        Returns:
            List of set instances ordered by set_number
        """
        stmt = (
            select(Set)
            .where(Set.workout_id == workout_id)
            .order_by(Set.set_number)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_recent_sets_for_exercise(
        self, user_id: UUID, exercise_id: UUID, limit: int = 30
    ) -> list[Set]:
        """
        Get recent sets for a specific exercise and user.

        Args:
            user_id: User UUID
            exercise_id: Exercise UUID
            limit: Maximum number of records to return

        Returns:
            List of set instances ordered by logged_at DESC
        """
        stmt = (
            select(Set)
            .where(Set.user_id == user_id, Set.exercise_id == exercise_id)
            .order_by(Set.logged_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_sets_for_workout_and_exercise(
        self, workout_id: UUID, exercise_id: UUID
    ) -> list[Set]:
        """
        Get all sets for a specific workout and exercise.

        Args:
            workout_id: Workout UUID
            exercise_id: Exercise UUID

        Returns:
            List of set instances ordered by set_number
        """
        stmt = (
            select(Set)
            .where(Set.workout_id == workout_id, Set.exercise_id == exercise_id)
            .order_by(Set.set_number)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_sets_in_workout(self, workout_id: UUID) -> int:
        """
        Count total sets in a workout (all exercises).

        Args:
            workout_id: Workout UUID

        Returns:
            Number of sets
        """
        from sqlalchemy import func

        stmt = select(func.count(Set.id)).where(Set.workout_id == workout_id)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_max_weight_for_exercise(
        self, user_id: UUID, exercise_id: UUID
    ) -> float | None:
        """
        Get the maximum weight ever lifted for a user and exercise.

        Args:
            user_id: User UUID
            exercise_id: Exercise UUID

        Returns:
            Max weight_kg or None if no sets
        """
        from sqlalchemy import func

        stmt = (
            select(func.max(Set.weight_kg))
            .where(Set.user_id == user_id, Set.exercise_id == exercise_id)
        )
        result = await self.session.execute(stmt)
        value = result.scalar()
        return float(value) if value is not None else None
