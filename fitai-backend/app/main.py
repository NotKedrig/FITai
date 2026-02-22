import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from app.api.v1 import health as health_router
from app.api.v1.router import api_router
from app.config import get_settings
from app.core.middleware import RequestLoggingMiddleware, get_cors_origins

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info(
        "FitAI starting in %s mode, AI provider: %s",
        settings.ENVIRONMENT,
        settings.AI_PROVIDER,
    )
    yield
    # Place shutdown logic here (e.g. closing connections).


def create_app() -> FastAPI:
    settings = get_settings()
    docs = settings.ENVIRONMENT != "production"
    app = FastAPI(
        title="FitAI",
        lifespan=lifespan,
        docs_url="/docs" if docs else None,
        redoc_url="/redoc" if docs else None,
    )

    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
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
    app.include_router(health_router.router)  # GET /health at root

    return app


app = create_app()

