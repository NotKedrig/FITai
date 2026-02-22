"""Set service — log set and optional AI recommendation."""

import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import build_context
from app.ai.base import AIProvider, AIRecommendation, WorkoutContext
from app.models.set import Set
from app.models.workout import Workout
from app.repositories.recommendation_repo import RecommendationRepository
from app.repositories.set_repo import SetRepository
from app.repositories.workout_repo import WorkoutRepository
from app.schemas.recommendation import RecommendationResponse
from app.schemas.set import SetCreate, SetResponse, SetWithRecommendation
from app.services.rule_engine import get_minimal_fallback, get_rule_based_recommendation

logger = logging.getLogger(__name__)


def _ai_rec_to_response(rec: AIRecommendation) -> RecommendationResponse:
    return RecommendationResponse(
        suggested_weight_kg=rec.suggested_weight_kg,
        suggested_reps=rec.suggested_reps,
        explanation=rec.explanation,
        confidence=rec.confidence,
        model_used=rec.model_used,
        latency_ms=rec.latency_ms,
    )


async def log_set(
    workout_id: UUID,
    set_in: SetCreate,
    user_id: UUID,
    db: AsyncSession,
    ai_provider: AIProvider,
) -> SetWithRecommendation:
    """
    Log a set for an active workout and optionally attach an AI recommendation.

    - Verifies workout exists and belongs to user (403 if not).
    - Verifies workout is active (400 if ended).
    - Sets set_number as count of existing sets for this exercise in workout + 1.
    - Creates Set record.
    - If not warmup: builds context, gets AI recommendation (or rule-based fallback on any error), stores recommendation.
    - Returns SetWithRecommendation (recommendation None if warmup).
    """
    workout_repo = WorkoutRepository(db)
    set_repo = SetRepository(db)
    rec_repo = RecommendationRepository(db)

    workout = await workout_repo.get(workout_id)
    if workout is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found",
        )
    if workout.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to modify this workout",
        )
    if workout.ended_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workout has already ended",
        )

    current_sets = await set_repo.get_sets_for_workout_and_exercise(
        workout_id, set_in.exercise_id
    )
    set_number = len(current_sets) + 1

    set_data = {
        "workout_id": workout_id,
        "exercise_id": set_in.exercise_id,
        "user_id": user_id,
        "set_number": set_number,
        "weight_kg": set_in.weight_kg,
        "reps": set_in.reps,
        "rpe": set_in.rpe,
        "is_warmup": set_in.is_warmup,
    }
    new_set = await set_repo.create(set_data)
    await db.flush()
    await db.refresh(new_set)
    assert isinstance(new_set, Set)

    recommendation_response: RecommendationResponse | None = None

    if not set_in.is_warmup:
        ctx: WorkoutContext | None = None
        try:
            ctx = await build_context(
                workout_id, set_in.exercise_id, user_id, db
            )
        except Exception:
            pass  # ctx remains None

        if ctx is not None:
            try:
                rec: AIRecommendation = await ai_provider.get_recommendation(ctx)
                recommendation_response = _ai_rec_to_response(rec)
                provider_name = "gemini" if "gemini" in rec.model_used.lower() else "ai"
                await rec_repo.create({
                    "user_id": user_id,
                    "workout_id": workout_id,
                    "set_id": new_set.id,
                    "exercise_id": set_in.exercise_id,
                    "recommended_weight": rec.suggested_weight_kg,
                    "recommended_reps": rec.suggested_reps,
                    "explanation": rec.explanation,
                    "confidence": rec.confidence,
                    "ai_provider": provider_name,
                    "model_used": rec.model_used,
                    "latency_ms": rec.latency_ms,
                })
            except Exception as e:
                logger.exception("AI recommendation failed: %s", e)
                fallback_weight, fallback_reps, fallback_explanation = get_rule_based_recommendation(
                    ctx, set_in.weight_kg, set_in.reps, set_in.rpe
                )
                recommendation_response = RecommendationResponse(
                    suggested_weight_kg=fallback_weight,
                    suggested_reps=fallback_reps,
                    explanation=fallback_explanation,
                    confidence="low",
                    model_used="rule-based",
                    latency_ms=0,
                )
                await rec_repo.create({
                    "user_id": user_id,
                    "workout_id": workout_id,
                    "set_id": new_set.id,
                    "exercise_id": set_in.exercise_id,
                    "recommended_weight": fallback_weight,
                    "recommended_reps": fallback_reps,
                    "explanation": fallback_explanation,
                    "confidence": "low",
                    "ai_provider": "fallback",
                    "model_used": "rule-based",
                    "latency_ms": 0,
                })
        else:
            fallback_weight, fallback_reps, fallback_explanation = get_minimal_fallback(
                set_in.weight_kg, set_in.reps, set_in.rpe
            )
            recommendation_response = RecommendationResponse(
                suggested_weight_kg=fallback_weight,
                suggested_reps=fallback_reps,
                explanation=fallback_explanation,
                confidence="low",
                model_used="rule-based",
                latency_ms=0,
            )
            await rec_repo.create({
                "user_id": user_id,
                "workout_id": workout_id,
                "set_id": new_set.id,
                "exercise_id": set_in.exercise_id,
                "recommended_weight": fallback_weight,
                "recommended_reps": fallback_reps,
                "explanation": fallback_explanation,
                "confidence": "low",
                "ai_provider": "fallback",
                "model_used": "rule-based",
                "latency_ms": 0,
            })

    await db.commit()
    await db.refresh(new_set)

    return SetWithRecommendation(
        set=SetResponse.model_validate(new_set),
        recommendation=recommendation_response,
    )


async def get_sets_for_workout(
    workout_id: UUID, user_id: UUID, db: AsyncSession
) -> list[SetResponse]:
    """List sets for a workout. User must own the workout."""
    workout_repo = WorkoutRepository(db)
    set_repo = SetRepository(db)
    workout = await workout_repo.get(workout_id)
    if workout is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found",
        )
    if workout.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to view this workout",
        )
    sets = await set_repo.get_sets_for_workout(workout_id)
    return [SetResponse.model_validate(s) for s in sets]


async def delete_set(
    set_id: UUID, user_id: UUID, db: AsyncSession
) -> None:
    """Delete a set. User must own the set's workout. Returns 204."""
    set_repo = SetRepository(db)
    workout_repo = WorkoutRepository(db)
    s = await set_repo.get(set_id)
    if s is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Set not found",
        )
    if s.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to delete this set",
        )
    await set_repo.delete(set_id)
    await db.commit()
