"""Build WorkoutContext from workout, exercise, and DB state."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import WorkoutContext
from app.models.exercise import Exercise
from app.models.set import Set
from app.models.workout import Workout
from app.repositories.exercise_repo import ExerciseRepository
from app.repositories.set_repo import SetRepository
from app.repositories.workout_repo import WorkoutRepository

# Epley formula: estimated 1RM = weight * (1 + reps / 30)
def _epley_1rm(weight_kg: float, reps: int) -> float:
    return weight_kg * (1.0 + reps / 30.0)


async def build_context(
    workout_id: UUID,
    exercise_id: UUID,
    user_id: UUID,
    db: AsyncSession,
) -> WorkoutContext:
    """
    Build a fully populated WorkoutContext for AI recommendation.

    Fetches exercise, current session sets, last 3 sessions for this exercise,
    computes estimated 1RM (Epley from best set in recent history), max weight ever,
    total sets in current workout, and workout duration.
    """
    exercise_repo = ExerciseRepository(db)
    set_repo = SetRepository(db)
    workout_repo = WorkoutRepository(db)

    # 1. Fetch exercise details
    exercise = await exercise_repo.get(exercise_id)
    if not exercise:
        raise ValueError(f"Exercise {exercise_id} not found")
    assert isinstance(exercise, Exercise)

    # 2. Fetch workout (for started_at and to verify it exists)
    workout = await workout_repo.get(workout_id)
    if not workout:
        raise ValueError(f"Workout {workout_id} not found")
    assert isinstance(workout, Workout)
    if workout.user_id != user_id:
        raise ValueError("Workout does not belong to user")

    # 3. Fetch all sets for this exercise in the current workout session
    current_sets = await set_repo.get_sets_for_workout_and_exercise(
        workout_id, exercise_id
    )
    current_session_sets = [
        {
            "weight_kg": float(s.weight_kg),
            "reps": s.reps,
            "rpe": float(s.rpe) if s.rpe is not None else None,
            "set_number": s.set_number,
        }
        for s in current_sets
    ]

    # 4. Fetch last 3 workout sessions where this exercise was performed
    recent_sets = await set_repo.get_recent_sets_for_exercise(
        user_id, exercise_id, limit=60
    )
    # Group by workout_id; order groups by most recent set (logged_at desc)
    sets_by_workout: dict[UUID, list[Set]] = {}
    for s in recent_sets:
        wid = s.workout_id
        if wid not in sets_by_workout:
            sets_by_workout[wid] = []
        sets_by_workout[wid].append(s)
    # Most recent workout = first in recent_sets; preserve order of first occurrence
    # Exclude current workout so "recent sessions" are past sessions only
    seen_order: list[UUID] = []
    for s in recent_sets:
        if s.workout_id == workout_id:
            continue
        if s.workout_id not in seen_order:
            seen_order.append(s.workout_id)
    last_3_workout_ids = seen_order[:3]

    # Fetch workout rows for dates (single query for up to 3 IDs)
    recent_sessions: list[dict] = []
    if last_3_workout_ids:
        workouts_for_sessions = await workout_repo.get_many_by_id(last_3_workout_ids)
        workout_dates = {w.id: w.started_at for w in workouts_for_sessions}
        for i, wid in enumerate(last_3_workout_ids):
            session_sets = sets_by_workout.get(wid, [])
            if not session_sets:
                continue
            started_at = workout_dates.get(wid)
            date_str = (
                started_at.strftime("%Y-%m-%d") if started_at else ""
            )
            best = max(
                session_sets,
                key=lambda s: (float(s.weight_kg), s.reps),
            )
            session_summary = {
                "date": date_str,
                "sets": [
                    {
                        "weight_kg": float(s.weight_kg),
                        "reps": s.reps,
                        "rpe": float(s.rpe) if s.rpe is not None else None,
                    }
                    for s in session_sets
                ],
            }
            recent_sessions.append(session_summary)

    # 5. Compute estimated_1rm using Epley from best set across recent history
    estimated_1rm: float | None = None
    if recent_sets:
        best_epley = max(
            _epley_1rm(float(s.weight_kg), s.reps) for s in recent_sets
        )
        estimated_1rm = round(best_epley, 2)

    # 6. Fetch max_weight_ever for this user/exercise
    max_weight_ever = await set_repo.get_max_weight_for_exercise(
        user_id, exercise_id
    )

    # 7. Count total sets in current workout (all exercises)
    total_sets_today = await set_repo.count_sets_in_workout(workout_id)

    # 8. Compute workout_duration_minutes from workout.started_at to now()
    now = datetime.now(timezone.utc)
    started = workout.started_at
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    delta = now - started
    workout_duration_minutes = max(0, int(delta.total_seconds() / 60))

    return WorkoutContext(
        exercise_name=exercise.name,
        muscle_group=exercise.muscle_group,
        equipment_type=exercise.equipment_type or "",
        is_compound=exercise.is_compound,
        current_session_sets=current_session_sets,
        recent_sessions=recent_sessions,
        estimated_1rm=estimated_1rm,
        max_weight_ever=max_weight_ever,
        total_sets_today=total_sets_today,
        workout_duration_minutes=workout_duration_minutes,
    )
