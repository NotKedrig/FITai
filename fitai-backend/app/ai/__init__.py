from app.ai.base import AIProvider, AIRecommendation, WorkoutContext
from app.ai.context_builder import build_context
from app.ai.gemini_provider import GeminiProvider
from app.ai.ollama_provider import OllamaProvider
from app.ai.openai_provider import OpenAIProvider
from app.ai.prompt_builder import PromptBuilder

from app.config import Settings


def get_ai_provider(settings: Settings) -> AIProvider:
    match settings.AI_PROVIDER.lower():
        case "gemini":
            return GeminiProvider(
                api_key=settings.GEMINI_API_KEY or "",
                model=settings.GEMINI_MODEL,
            )
        case "openai":
            return OpenAIProvider()
        case "ollama":
            return OllamaProvider()
        case _:
            raise ValueError(
                f"Unknown AI_PROVIDER: {settings.AI_PROVIDER!r}. "
                "Use one of: gemini, openai, ollama"
            )


__all__ = [
    "AIProvider",
    "AIRecommendation",
    "WorkoutContext",
    "PromptBuilder",
    "GeminiProvider",
    "OllamaProvider",
    "OpenAIProvider",
    "get_ai_provider",
    "build_context",
]
