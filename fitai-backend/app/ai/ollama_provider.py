# Ollama provider — activate on GPU machine.

from app.ai.base import AIProvider, AIRecommendation, WorkoutContext


class OllamaProvider(AIProvider):
    """Ollama-backed AI provider (stub)."""

    async def get_recommendation(self, context: WorkoutContext) -> AIRecommendation:
        raise NotImplementedError("Ollama provider — activate on GPU machine.")

    async def health_check(self) -> bool:
        return False  # Not implemented; fail gracefully for health checks.
