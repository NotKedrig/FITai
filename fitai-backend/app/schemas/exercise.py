"""Schemas for Exercise API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ExerciseCreate(BaseModel):
    """Schema for creating an exercise."""

    name: str
    muscle_group: str
    equipment_type: str | None = None
    is_compound: bool = False


class ExerciseResponse(BaseModel):
    """Schema for exercise response (all fields + id + created_at)."""

    id: UUID
    name: str
    muscle_group: str
    equipment_type: str | None
    is_compound: bool
    created_at: datetime

    model_config = {"from_attributes": True}
