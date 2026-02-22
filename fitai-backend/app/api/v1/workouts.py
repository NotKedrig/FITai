"""Workout API routes — all require authentication."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.workout import WorkoutCreate, WorkoutResponse, WorkoutUpdate
from app.services import workout_service

router = APIRouter()


@router.post(
    "",
    response_model=WorkoutResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_workout(
    workout_in: WorkoutCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkoutResponse:
    """Start a new workout for the current user."""
    workout = await workout_service.start_workout(
        workout_in, current_user.id, db
    )
    return WorkoutResponse.model_validate(workout)


@router.get("", response_model=list[WorkoutResponse])
async def list_workouts(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[WorkoutResponse]:
    """List workouts for the current user (paginated)."""
    workouts = await workout_service.get_user_workouts(
        current_user.id, skip=skip, limit=limit, db=db
    )
    return [WorkoutResponse.model_validate(w) for w in workouts]


@router.get("/{workout_id}", response_model=WorkoutResponse)
async def get_workout(
    workout_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkoutResponse:
    """Get a single workout by id (own workouts only)."""
    workout = await workout_service.get_workout(
        workout_id, current_user.id, db
    )
    return WorkoutResponse.model_validate(workout)


@router.post("/{workout_id}/end", response_model=WorkoutResponse)
async def end_workout(
    workout_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkoutResponse:
    """End a workout (sets ended_at to now)."""
    workout = await workout_service.end_workout(
        workout_id, current_user.id, db
    )
    return WorkoutResponse.model_validate(workout)


@router.patch("/{workout_id}", response_model=WorkoutResponse)
async def update_workout(
    workout_id: UUID,
    update_in: WorkoutUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkoutResponse:
    """Update a workout (name, notes, or ended_at)."""
    workout = await workout_service.update_workout(
        workout_id, current_user.id, update_in, db
    )
    return WorkoutResponse.model_validate(workout)
