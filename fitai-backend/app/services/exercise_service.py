"""Exercise service — business logic for exercises (uses repository layer only)."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exercise import Exercise
from app.repositories.exercise_repo import ExerciseRepository
from app.schemas.exercise import ExerciseCreate


async def create_exercise(
    exercise_in: ExerciseCreate, db: AsyncSession
) -> Exercise:
    """
    Create a new global exercise.

    Args:
        exercise_in: Exercise creation schema
        db: Database session

    Returns:
        Created Exercise instance (global, no created_by)
    """
    repo = ExerciseRepository(db)
    data = {
        "name": exercise_in.name,
        "muscle_group": exercise_in.muscle_group,
        "equipment_type": exercise_in.equipment_type,
        "is_compound": exercise_in.is_compound,
        "is_global": True,
        "created_by": None,
    }
    exercise = await repo.create(data)
    await db.commit()
    await db.refresh(exercise)
    return exercise


async def get_exercise(exercise_id: UUID, db: AsyncSession) -> Exercise | None:
    """
    Get an exercise by id.

    Args:
        exercise_id: Exercise UUID
        db: Database session

    Returns:
        Exercise instance or None
    """
    repo = ExerciseRepository(db)
    return await repo.get(exercise_id)


async def get_exercise_or_404(
    exercise_id: UUID, db: AsyncSession
) -> Exercise:
    """
    Get an exercise by id or raise 404.

    Args:
        exercise_id: Exercise UUID
        db: Database session

    Returns:
        Exercise instance

    Raises:
        HTTPException: 404 if not found
    """
    exercise = await get_exercise(exercise_id, db)
    if exercise is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found",
        )
    return exercise


async def list_exercises(
    search: str | None, db: AsyncSession
) -> list[Exercise]:
    """
    List global exercises with optional name search.

    Args:
        search: Optional search query for name
        db: Database session

    Returns:
        List of Exercise instances
    """
    repo = ExerciseRepository(db)
    return await repo.get_global_exercises_with_search(search=search)
