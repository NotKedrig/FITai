"""Health check endpoint — no authentication required."""

import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.dependencies import get_ai_provider

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health(
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Unified health check: DB and AI.
    Returns 200 if all ok, 503 if any component fails.
    """
    db_status = "error"
    ai_status = "error"

    try:
        await db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        logger.warning("Health check DB failed: %s", e)

    try:
        provider = get_ai_provider()
        ai_ok = await provider.health_check()
        ai_status = "ok" if ai_ok else "error"
        if not ai_ok:
            logger.warning("Health check AI failed: provider returned False")
    except Exception as e:
        logger.warning("Health check AI failed: %s", e)

    overall = "ok" if (db_status == "ok" and ai_status == "ok") else "degraded"
    status_code = 200 if overall == "ok" else 503

    return JSONResponse(
        content={"status": overall, "db": db_status, "ai": ai_status},
        status_code=status_code,
    )
