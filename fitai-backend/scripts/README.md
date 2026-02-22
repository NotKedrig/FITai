# Scripts

## Migrations (required for set logging + AI recommendation)

The set-logging endpoint writes to the `recommendations` table and expects a `confidence` column. Ensure migrations are applied in the same DB the API uses:

- **Docker:** `docker compose exec api python run_alembic.py upgrade head` (or `alembic upgrade head` if run from inside the container).
- **Local:** from `fitai-backend`, run `alembic upgrade head` (or `python run_alembic.py upgrade head`).

If you see **500 Internal Server Error** when logging a set, check the response body for the error message (e.g. missing column); apply the migration that adds `recommendations.confidence` if needed.

## Seed global exercises

The API’s `GET /api/v1/exercises` (and `?search=...`) reads from the `exercises` table. If that table is empty, the response will be `[]`. Seed it with:

**Docker (use the same DB as the API):**  
`docker-compose.yml` mounts `./scripts` into the api container. If you just added that volume, recreate the api container once: `docker compose up -d api`. Then:

```bash
docker compose exec api python scripts/seed_exercises.py
```

**Local (ensure `.env` has `DATABASE_URL` pointing at the same DB as the API, e.g. `postgresql+asyncpg://fitai:fitai@localhost:5432/fitai`):**

```bash
# from fitai-backend
uv run python scripts/seed_exercises.py
# or
PYTHONPATH=. python scripts/seed_exercises.py
```

The seed script is idempotent: if there are already 10+ global exercises, it skips inserting.
