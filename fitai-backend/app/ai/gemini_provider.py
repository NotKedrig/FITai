"""Gemini-backed AI provider for set recommendations."""

import json
import time
from typing import Any

from google import genai
from google.genai import types

from app.ai.base import AIProvider, AIRecommendation, WorkoutContext
from app.ai.prompt_builder import PromptBuilder

VALID_CONFIDENCE = frozenset({"high", "medium", "low"})


class GeminiProvider(AIProvider):
    """AI provider using Google Gemini (async via client.aio)."""

    def __init__(self, api_key: str, model: str) -> None:
        self._config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.3,
            max_output_tokens=512,
            system_instruction=PromptBuilder.SYSTEM_PROMPT,
        )
        self.model_name = model
        if api_key and (isinstance(api_key, str) and api_key.strip()):
            try:
                self._client = genai.Client(api_key=api_key)
            except Exception:
                self._client = None
        else:
            self._client = None

    async def get_recommendation(self, context: WorkoutContext) -> AIRecommendation:
        if self._client is None:
            raise ValueError("Gemini API key not configured")
        prompt = PromptBuilder.build_recommendation_prompt(context)
        start = time.perf_counter()

        response = await self._client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=self._config,
        )
        if not response.text:
            raise ValueError("Gemini returned empty response")

        raw_response = response.text
        latency_ms = int((time.perf_counter() - start) * 1000)

        try:
            data: dict[str, Any] = json.loads(raw_response)
        except json.JSONDecodeError as e:
            raise ValueError(f"Gemini response is not valid JSON: {e}") from e

        suggested_weight_kg = data.get("suggested_weight_kg")
        suggested_reps = data.get("suggested_reps")
        explanation = data.get("explanation")
        confidence = data.get("confidence")

        if not isinstance(suggested_weight_kg, (int, float)):
            raise ValueError(
                f"Invalid suggested_weight_kg: expected number, got {type(suggested_weight_kg).__name__}"
            )
        if not isinstance(suggested_reps, int):
            raise ValueError(
                f"Invalid suggested_reps: expected int, got {type(suggested_reps).__name__}"
            )
        if not isinstance(explanation, str) or not explanation.strip():
            raise ValueError(
                "Invalid explanation: expected non-empty string"
            )
        if confidence not in VALID_CONFIDENCE:
            raise ValueError(
                f"Invalid confidence: expected one of {sorted(VALID_CONFIDENCE)}, got {confidence!r}"
            )

        return AIRecommendation(
            suggested_weight_kg=float(suggested_weight_kg),
            suggested_reps=int(suggested_reps),
            explanation=explanation.strip(),
            confidence=confidence,
            raw_response=raw_response,
            latency_ms=latency_ms,
            model_used=self.model_name,
        )

    async def health_check(self) -> bool:
        if self._client is None:
            return False
        try:
            await self._client.aio.models.generate_content(
                model=self.model_name,
                contents="Reply with OK.",
            )
            return True
        except Exception:
            return False