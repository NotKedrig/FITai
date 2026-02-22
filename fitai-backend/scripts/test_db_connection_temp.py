"""
Temporary script to test database connection in isolation.
Do not commit permanently — delete after diagnostics.

Run from fitai-backend with DATABASE_URL set:
  uv run python scripts/test_db_connection_temp.py
  or: PYTHONPATH=. python scripts/test_db_connection_temp.py
"""
import asyncio
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import get_settings
from app.db.database import _ensure_async_url


async def test():
    settings = get_settings()
    url = _ensure_async_url(settings.DATABASE_URL)
    print("Resolved URL (scheme hidden):", url.split("@")[-1] if "@" in url else url[:50] + "...")
    engine = create_async_engine(url)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("OK: Database connection succeeded.")
    except Exception as e:
        print("FAIL:", type(e).__name__, str(e))
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test())
