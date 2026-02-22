"""Stats service — user and exercise aggregations (SQL only, no Python loops over records)."""

from datetime import date, timedelta, timezone
from uuid import UUID

from sqlalchemy import Date, cast, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exercise import Exercise
from app.models.set import Set
from app.models.workout import Workout


async def get_exercise_stats(
    user_id: UUID,
    exercise_id: UUID,
    db: AsyncSession,
) -> dict:
    """
    Aggregate stats for a user's exercise in a single query, then Epley 1RM from best set.

    Returns dict with: estimated_1rm, max_weight_kg, total_volume_kg, total_sets,
    sessions_count, last_session_date (ISO).
    """
    # Single aggregation query
    agg = (
        select(
            func.max(Set.weight_kg).label("max_weight_kg"),
            func.coalesce(func.sum(Set.weight_kg * Set.reps), 0).label("total_volume_kg"),
            func.count(Set.id).label("total_sets"),
            func.count(distinct(Set.workout_id)).label("sessions_count"),
            func.max(Set.logged_at).label("last_session_date"),
        )
        .where(Set.user_id == user_id, Set.exercise_id == exercise_id)
    )
    row = (await db.execute(agg)).one_or_none()

    if row is None or row.total_sets == 0:
        return {
            "estimated_1rm": None,
            "max_weight_kg": None,
            "total_volume_kg": None,
            "total_sets": 0,
            "sessions_count": 0,
            "last_session_date": None,
        }

    max_weight_kg = float(row.max_weight_kg) if row.max_weight_kg is not None else None
    total_volume_kg = float(row.total_volume_kg) if row.total_volume_kg is not None else None
    total_sets = int(row.total_sets)
    sessions_count = int(row.sessions_count)
    last_session_date: str | None = None
    if row.last_session_date is not None:
        dt = row.last_session_date
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        last_session_date = dt.date().isoformat()

    # Reps for best set (max weight) for Epley: estimated_1rm = max_weight_kg * (1 + reps/30)
    reps_row = (
        await db.execute(
            select(Set.reps)
            .where(
                Set.user_id == user_id,
                Set.exercise_id == exercise_id,
                Set.weight_kg == row.max_weight_kg,
            )
            .order_by(Set.reps.desc())
            .limit(1)
        )
    ).one_or_none()

    estimated_1rm: float | None = None
    if max_weight_kg is not None and reps_row is not None:
        reps = int(reps_row[0])
        estimated_1rm = round(max_weight_kg * (1 + reps / 30), 2)

    return {
        "estimated_1rm": estimated_1rm,
        "max_weight_kg": max_weight_kg,
        "total_volume_kg": total_volume_kg,
        "total_sets": total_sets,
        "sessions_count": sessions_count,
        "last_session_date": last_session_date,
    }


async def get_user_overview(
    user_id: UUID,
    db: AsyncSession,
) -> dict:
    """
    User overview stats: workouts count, sets count, volume, most trained muscle,
    favourite exercise, active streak (consecutive days ending today).
    """
    # total_workouts: COUNT workouts where ended_at IS NOT NULL
    workouts_count_row = (
        await db.execute(
            select(func.count(Workout.id)).where(
                Workout.user_id == user_id,
                Workout.ended_at.isnot(None),
            )
        )
    ).scalar()
    total_workouts = int(workouts_count_row or 0)

    # total_sets, total_volume_kg
    sets_row = (
        await db.execute(
            select(
                func.count(Set.id).label("total_sets"),
                func.coalesce(func.sum(Set.weight_kg * Set.reps), 0).label("total_volume_kg"),
            ).where(Set.user_id == user_id)
        )
    ).one()
    total_sets = int(sets_row.total_sets or 0)
    total_volume_kg = float(sets_row.total_volume_kg or 0)

    # most_trained_muscle: muscle_group with highest set count (join sets -> exercises)
    muscle_row = (
        await db.execute(
            select(Exercise.muscle_group)
            .select_from(Set)
            .join(Exercise, Set.exercise_id == Exercise.id)
            .where(Set.user_id == user_id)
            .group_by(Exercise.muscle_group)
            .order_by(func.count(Set.id).desc())
            .limit(1)
        )
    ).one_or_none()
    most_trained_muscle: str | None = muscle_row[0] if muscle_row else None

    # favourite_exercise: exercise name with highest set count
    fav_row = (
        await db.execute(
            select(Exercise.name)
            .select_from(Set)
            .join(Exercise, Set.exercise_id == Exercise.id)
            .where(Set.user_id == user_id)
            .group_by(Exercise.id, Exercise.name)
            .order_by(func.count(Set.id).desc())
            .limit(1)
        )
    ).one_or_none()
    favourite_exercise: str | None = fav_row[0] if fav_row else None

    # active_streak_days: distinct workout dates (ended_at date), then Python streak
    dates_result = await db.execute(
        select(cast(Workout.ended_at, Date)).where(
            Workout.user_id == user_id,
            Workout.ended_at.isnot(None),
        )
    )
    workout_dates = {r[0] for r in dates_result.all() if r[0] is not None}

    active_streak_days = 0
    if workout_dates:
        today = date.today()
        d = today
        while d in workout_dates:
            active_streak_days += 1
            d = d - timedelta(days=1)

    return {
        "total_workouts": total_workouts,
        "total_sets": total_sets,
        "total_volume_kg": total_volume_kg,
        "most_trained_muscle": most_trained_muscle,
        "favourite_exercise": favourite_exercise,
        "active_streak_days": active_streak_days,
    }
