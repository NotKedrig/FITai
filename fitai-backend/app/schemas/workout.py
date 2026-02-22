"""Schemas for Workout API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class WorkoutCreate(BaseModel):
    """Schema for starting a workout."""

    name: str | None = None
    notes: str | None = None


class WorkoutUpdate(BaseModel):
    """Schema for updating a workout (e.g. end workout, edit notes)."""

    ended_at: datetime | None = None
    notes: str | None = None
    name: str | None = None


class WorkoutResponse(BaseModel):
    """Schema for workout response (all fields + id + user_id + started_at)."""

    id: UUID
    user_id: UUID
    name: str | None
    started_at: datetime
    ended_at: datetime | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
