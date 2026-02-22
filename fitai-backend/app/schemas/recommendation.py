"""Schemas for Recommendation API."""

from pydantic import BaseModel


class RecommendationResponse(BaseModel):
    """Schema for AI recommendation in API response."""

    suggested_weight_kg: float
    suggested_reps: int
    explanation: str
    confidence: str
    model_used: str
    latency_ms: int
