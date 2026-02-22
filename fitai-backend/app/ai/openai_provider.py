"""OpenAI-backed AI provider (stub)."""

from app.ai.base import AIProvider, AIRecommendation, WorkoutContext


class OpenAIProvider(AIProvider):
    """OpenAI-backed AI provider (stub)."""

    async def get_recommendation(self, context: WorkoutContext) -> AIRecommendation:
        raise NotImplementedError("OpenAI provider not implemented yet.")

    async def health_check(self) -> bool:
        raise NotImplementedError("OpenAI provider not implemented yet.")
