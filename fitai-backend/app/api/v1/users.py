"""User API routes — profile and stats; all require authentication."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse
from app.services import exercise_service, stats_service

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Return the current authenticated user's profile (no password)."""
    return UserResponse.model_validate(current_user)


@router.get("/me/stats")
async def get_my_overview_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return overview stats for the current user."""
    return await stats_service.get_user_overview(current_user.id, db)


@router.get("/me/stats/{exercise_id}")
async def get_my_exercise_stats(
    exercise_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return exercise-specific stats for the current user. 404 if exercise does not exist."""
    await exercise_service.get_exercise_or_404(exercise_id, db)
    return await stats_service.get_exercise_stats(
        current_user.id, exercise_id, db
    )
