"""
Seed global exercises (20 total, spec-standardized).

Run against the same DB as the API:

  In Docker (recommended):
    docker compose exec api python scripts/seed_exercises.py

  Local (set DATABASE_URL in .env to match API):
    From fitai-backend: uv run python scripts/seed_exercises.py
    Or: PYTHONPATH=. python scripts/seed_exercises.py

Uses repository layer; requires DATABASE_URL and migrations applied.
Idempotent: checks each exercise by name before inserting. Safe to run multiple times.
"""
import asyncio
import logging
import sys
from pathlib import Path

from sqlalchemy import select

# Ensure app is on path when run as script
root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from app.db.database import AsyncSessionLocal
from app.models.exercise import Exercise
from app.repositories.exercise_repo import ExerciseRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 20 exercises: name, muscle_group, equipment_type (spec-exact). is_compound set by movement type.
SEED_EXERCISES = [
    {"name": "Barbell Bench Press", "muscle_group": "chest", "equipment_type": "barbell", "is_compound": True},
    {"name": "Squat", "muscle_group": "legs", "equipment_type": "barbell", "is_compound": True},
    {"name": "Deadlift", "muscle_group": "back", "equipment_type": "barbell", "is_compound": True},
    {"name": "Overhead Press", "muscle_group": "shoulders", "equipment_type": "barbell", "is_compound": True},
    {"name": "Pull Up", "muscle_group": "back", "equipment_type": "bodyweight", "is_compound": True},
    {"name": "Barbell Row", "muscle_group": "back", "equipment_type": "barbell", "is_compound": True},
    {"name": "Dumbbell Curl", "muscle_group": "arms", "equipment_type": "dumbbell", "is_compound": False},
    {"name": "Tricep Pushdown", "muscle_group": "arms", "equipment_type": "cable", "is_compound": False},
    {"name": "Leg Press", "muscle_group": "legs", "equipment_type": "machine", "is_compound": True},
    {"name": "Lat Pulldown", "muscle_group": "back", "equipment_type": "cable", "is_compound": True},
    {"name": "Romanian Deadlift", "muscle_group": "legs", "equipment_type": "barbell", "is_compound": True},
    {"name": "Incline Dumbbell Press", "muscle_group": "chest", "equipment_type": "dumbbell", "is_compound": True},
    {"name": "Cable Row", "muscle_group": "back", "equipment_type": "cable", "is_compound": True},
    {"name": "Face Pull", "muscle_group": "shoulders", "equipment_type": "cable", "is_compound": False},
    {"name": "Hip Thrust", "muscle_group": "legs", "equipment_type": "barbell", "is_compound": True},
    {"name": "Lunges", "muscle_group": "legs", "equipment_type": "bodyweight", "is_compound": True},
    {"name": "Leg Curl", "muscle_group": "legs", "equipment_type": "machine", "is_compound": False},
    {"name": "Leg Extension", "muscle_group": "legs", "equipment_type": "machine", "is_compound": False},
    {"name": "Dumbbell Row", "muscle_group": "back", "equipment_type": "dumbbell", "is_compound": True},
    {"name": "Arnold Press", "muscle_group": "shoulders", "equipment_type": "dumbbell", "is_compound": True},
]


async def main() -> None:
    async with AsyncSessionLocal() as session:
        repo = ExerciseRepository(session)
        inserted = 0
        for data in SEED_EXERCISES:
            existing = await session.execute(
                select(Exercise).where(Exercise.name == data["name"]).limit(1)
            )
            if existing.scalar_one_or_none() is not None:
                continue
            await repo.create({
                **data,
                "is_global": True,
                "created_by": None,
            })
            inserted += 1
        await session.commit()
    logger.info("Seed complete: %s new exercises (total spec set: 20).", inserted)


if __name__ == "__main__":
    asyncio.run(main())
