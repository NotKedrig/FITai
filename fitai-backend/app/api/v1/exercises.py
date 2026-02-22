"""Exercise API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.exercise import ExerciseCreate, ExerciseResponse
from app.services import exercise_service

router = APIRouter()


@router.get("", response_model=list[ExerciseResponse])
async def list_exercises(
    search: str | None = Query(None, description="Filter by name"),
    db: AsyncSession = Depends(get_db),
) -> list[ExerciseResponse]:
    """List global exercises with optional name search."""
    exercises = await exercise_service.list_exercises(search=search, db=db)
    return [ExerciseResponse.model_validate(e) for e in exercises]


@router.post(
    "",
    response_model=ExerciseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_exercise(
    exercise_in: ExerciseCreate,
    db: AsyncSession = Depends(get_db),
) -> ExerciseResponse:
    """Create a new global exercise."""
    exercise = await exercise_service.create_exercise(exercise_in, db)
    return ExerciseResponse.model_validate(exercise)


@router.get("/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise(
    exercise_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ExerciseResponse:
    """Get an exercise by id."""
    exercise = await exercise_service.get_exercise_or_404(exercise_id, db)
    return ExerciseResponse.model_validate(exercise)
