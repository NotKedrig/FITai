"""Workout service — business logic for workouts (uses repository layer only)."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workout import Workout
from app.repositories.workout_repo import WorkoutRepository
from app.schemas.workout import WorkoutCreate, WorkoutUpdate


async def start_workout(
    workout_in: WorkoutCreate, user_id: UUID, db: AsyncSession
) -> Workout:
    """
    Start a new workout for the user.

    Args:
        workout_in: Optional name and notes
        user_id: Current user UUID
        db: Database session

    Returns:
        Created Workout instance with started_at set to now
    """
    repo = WorkoutRepository(db)
    now = datetime.now(timezone.utc)
    data = {
        "user_id": user_id,
        "started_at": now,
        "name": workout_in.name,
        "notes": workout_in.notes,
    }
    workout = await repo.create(data)
    await db.commit()
    await db.refresh(workout)
    return workout


async def end_workout(
    workout_id: UUID, user_id: UUID, db: AsyncSession
) -> Workout:
    """
    End a workout by setting ended_at to now.

    Args:
        workout_id: Workout UUID
        user_id: Current user UUID (must own the workout)
        db: Database session

    Returns:
        Updated Workout instance

    Raises:
        HTTPException: 404 if workout not found, 403 if wrong user
    """
    repo = WorkoutRepository(db)
    workout = await repo.get(workout_id)
    if workout is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found",
        )
    if workout.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to modify this workout",
        )
    now = datetime.now(timezone.utc)
    await repo.update(workout_id, {"ended_at": now})
    await db.commit()
    await db.refresh(workout)
    return workout


async def get_workout(
    workout_id: UUID, user_id: UUID, db: AsyncSession
) -> Workout:
    """
    Get a single workout by id. User can only see their own.

    Args:
        workout_id: Workout UUID
        user_id: Current user UUID
        db: Database session

    Returns:
        Workout instance

    Raises:
        HTTPException: 404 if not found, 403 if wrong user
    """
    repo = WorkoutRepository(db)
    workout = await repo.get(workout_id)
    if workout is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found",
        )
    if workout.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to view this workout",
        )
    return workout


async def get_user_workouts(
    user_id: UUID,
    skip: int,
    limit: int,
    db: AsyncSession,
) -> list[Workout]:
    """
    Get workouts for the current user with pagination.

    Args:
        user_id: Current user UUID
        skip: Number of records to skip
        limit: Maximum number of records
        db: Database session

    Returns:
        List of Workout instances
    """
    repo = WorkoutRepository(db)
    return await repo.get_user_workouts(user_id, skip=skip, limit=limit)


async def update_workout(
    workout_id: UUID,
    user_id: UUID,
    update_in: WorkoutUpdate,
    db: AsyncSession,
) -> Workout:
    """
    Update a workout (e.g. name, notes). User can only update their own.

    Args:
        workout_id: Workout UUID
        user_id: Current user UUID
        update_in: Fields to update (only non-None applied)
        db: Database session

    Returns:
        Updated Workout instance

    Raises:
        HTTPException: 404 if not found, 403 if wrong user
    """
    repo = WorkoutRepository(db)
    workout = await repo.get(workout_id)
    if workout is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found",
        )
    if workout.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to modify this workout",
        )
    payload = update_in.model_dump(exclude_unset=True)
    if not payload:
        return workout
    updated = await repo.update(workout_id, payload)
    await db.commit()
    if updated:
        await db.refresh(updated)
        return updated
    return workout
