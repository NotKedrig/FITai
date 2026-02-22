You are helping me build FitAI — a production-quality workout tracking backend.
Tech stack: FastAPI (Python 3.11), PostgreSQL 16, SQLAlchemy 2.0 async,
Alembic, Pydantic v2, Docker Compose (Windows host).

Rules you must follow at all times:

1. Use async SQLAlchemy throughout — never use sync Session.
2. Never put business logic in route handlers — use service layer.
3. Never hardcode credentials — all config via pydantic-settings + .env.
4. Use UUID primary keys everywhere (gen_random_uuid() in Postgres).
5. Never use WidthType.PERCENTAGE in any table definitions.
6. All models must have created_at TIMESTAMPTZ with server default.
7. Alembic migrations are the ONLY way to change the schema.
8. Never run raw SQL to create tables — Alembic only.
9. Follow this folder structure exactly: app/api/v1/, app/models/,
   app/schemas/, app/services/, app/repositories/, app/ai/, app/db/
10. After writing any file, confirm what you created and why.
11. All database access must go through repository layer — services must not query models directly.
12. Password hashing must use passlib[bcrypt], JWT must use python-jose, never implement crypto manually.
