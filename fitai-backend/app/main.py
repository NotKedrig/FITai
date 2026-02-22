import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    # Place startup logic here (e.g. DB/AI client init) using settings.
    yield
    # Place shutdown logic here (e.g. closing connections).


def create_app() -> FastAPI:
    app = FastAPI(
        title="FitAI",
        lifespan=lifespan,
    )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Capture unhandled exceptions and return JSON with detail for debugging."""
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {str(exc)}"},
        )

    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health")
    async def health() -> dict:
        """Basic health check. Use /health/db to verify database connectivity."""
        return {"status": "ok"}

    @app.get("/health/db")
    async def health_db() -> dict:
        """Verify database connectivity."""
        try:
            from sqlalchemy import text
            from app.db.database import AsyncSessionLocal
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
            return {"status": "ok", "database": "connected"}
        except Exception as e:
            return {"status": "error", "database": str(e)}

    return app


app = create_app()

