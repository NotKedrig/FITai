"""AI abstraction layer: context, recommendation types, and provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class WorkoutContext:
    """Context passed to the AI for generating a set recommendation."""

    exercise_name: str
    muscle_group: str
    equipment_type: str
    is_compound: bool
    current_session_sets: list[dict]  # {weight_kg, reps, rpe, set_number}
    recent_sessions: list[dict]  # last 3 sessions summary
    estimated_1rm: float | None
    max_weight_ever: float | None
    total_sets_today: int
    workout_duration_minutes: int
    seconds_since_last_set: int | None = None
    target_rpe: float | None = None

@dataclass
class AIRecommendation:
    """Structured recommendation returned by an AI provider."""

    suggested_weight_kg: float
    suggested_reps: int
    explanation: str
    confidence: str  # "high" | "medium" | "low"
    raw_response: str
    latency_ms: int
    model_used: str


class AIProvider(ABC):
    """Abstract base for AI providers (e.g. Gemini, OpenAI)."""

    @abstractmethod
    async def get_recommendation(self, context: WorkoutContext) -> AIRecommendation:
        """Return a single set recommendation for the given workout context."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the provider is reachable and usable."""
        ...
