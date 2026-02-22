"""Set API routes — log set (with AI recommendation), list sets, delete set."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import AIProvider
from app.db.database import get_db
from app.dependencies import get_ai_provider, get_current_user
from app.models.user import User
from app.schemas.set import SetCreate, SetResponse, SetWithRecommendation
from app.services import set_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/workouts/{workout_id}/sets",
    response_model=SetWithRecommendation,
    status_code=status.HTTP_201_CREATED,
)
async def log_set(
    workout_id: UUID,
    set_in: SetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ai_provider: AIProvider = Depends(get_ai_provider),
) -> SetWithRecommendation:
    """Log a set for an active workout; returns the set and optional AI recommendation (None if warmup or AI failed)."""
    try:
        return await set_service.log_set(
            workout_id, set_in, current_user.id, db, ai_provider
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Log set failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Log set failed: {e!s}",
        ) from e


@router.get(
    "/workouts/{workout_id}/sets",
    response_model=list[SetResponse],
)
async def list_sets(
    workout_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SetResponse]:
    """List all sets for a workout (own workouts only)."""
    return await set_service.get_sets_for_workout(
        workout_id, current_user.id, db
    )


@router.delete(
    "/sets/{set_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_set(
    set_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a set (own sets only)."""
    await set_service.delete_set(set_id, current_user.id, db)
