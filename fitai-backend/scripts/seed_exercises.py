"""
Seed global exercises.

Run against the same DB as the API:

  In Docker (recommended):
    docker compose exec api python scripts/seed_exercises.py

  Local (set DATABASE_URL in .env to match API, e.g. postgresql+asyncpg://fitai:fitai@localhost:5432/fitai):
    From fitai-backend: uv run python scripts/seed_exercises.py
    Or: PYTHONPATH=. python scripts/seed_exercises.py

Uses repository layer only; requires DATABASE_URL and migrations applied.
Idempotent: skips if 10+ global exercises already exist.
"""
import asyncio
import sys
from pathlib import Path

# Ensure app is on path when run as script
root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from app.db.database import AsyncSessionLocal
from app.repositories.exercise_repo import ExerciseRepository

MIN_SEED_COUNT = 10

SEED_EXERCISES = [
    {"name": "Barbell Bench Press", "muscle_group": "Chest", "equipment_type": "barbell", "is_compound": True, "is_global": True, "created_by": None},
    {"name": "Bench Press", "muscle_group": "Chest", "equipment_type": "Barbell", "is_compound": True, "is_global": True, "created_by": None},
    {"name": "Squat", "muscle_group": "Legs", "equipment_type": "Barbell", "is_compound": True, "is_global": True, "created_by": None},
    {"name": "Deadlift", "muscle_group": "Back", "equipment_type": "Barbell", "is_compound": True, "is_global": True, "created_by": None},
    {"name": "Overhead Press", "muscle_group": "Shoulders", "equipment_type": "Barbell", "is_compound": True, "is_global": True, "created_by": None},
    {"name": "Barbell Row", "muscle_group": "Back", "equipment_type": "Barbell", "is_compound": True, "is_global": True, "created_by": None},
    {"name": "Pull-up", "muscle_group": "Back", "equipment_type": "Bodyweight", "is_compound": True, "is_global": True, "created_by": None},
    {"name": "Dumbbell Curl", "muscle_group": "Biceps", "equipment_type": "Dumbbell", "is_compound": False, "is_global": True, "created_by": None},
    {"name": "Tricep Pushdown", "muscle_group": "Triceps", "equipment_type": "Cable", "is_compound": False, "is_global": True, "created_by": None},
    {"name": "Leg Press", "muscle_group": "Legs", "equipment_type": "Machine", "is_compound": True, "is_global": True, "created_by": None},
    {"name": "Romanian Deadlift", "muscle_group": "Hamstrings", "equipment_type": "Barbell", "is_compound": True, "is_global": True, "created_by": None},
    {"name": "Lateral Raise", "muscle_group": "Shoulders", "equipment_type": "Dumbbell", "is_compound": False, "is_global": True, "created_by": None},
    {"name": "Cable Fly", "muscle_group": "Chest", "equipment_type": "Cable", "is_compound": False, "is_global": True, "created_by": None},
]


async def main() -> None:
    async with AsyncSessionLocal() as session:
        repo = ExerciseRepository(session)
        existing = await repo.get_global_exercises_with_search(search=None)
        if len(existing) >= MIN_SEED_COUNT:
            print(f"Already seeded ({len(existing)} global exercises). Skip.")
            return
        for data in SEED_EXERCISES:
            await repo.create(data)
        await session.commit()
    print(f"Seeded {len(SEED_EXERCISES)} global exercises.")


if __name__ == "__main__":
    asyncio.run(main())
