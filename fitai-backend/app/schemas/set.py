"""Schemas for Set API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.recommendation import RecommendationResponse


class SetCreate(BaseModel):
    """Schema for logging a set."""

    exercise_id: UUID
    weight_kg: float
    reps: int
    rpe: float | None = None
    is_warmup: bool = False


class SetResponse(BaseModel):
    """Schema for set response (all fields + id + logged_at)."""

    id: UUID
    workout_id: UUID
    exercise_id: UUID
    user_id: UUID
    set_number: int
    weight_kg: float
    reps: int
    rpe: float | None
    is_warmup: bool
    logged_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class SetWithRecommendation(BaseModel):
    """Response for logging a set: the set plus optional AI recommendation (None if warmup or AI failed)."""

    set: SetResponse
    recommendation: RecommendationResponse | None = None
