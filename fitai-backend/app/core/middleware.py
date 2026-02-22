"""CORS and request logging middleware."""

import logging
import time
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.config import get_settings

logger = logging.getLogger(__name__)


def get_cors_origins() -> list[str]:
    """
    Build CORS allow_origins list from settings.
    Only allow '*' when ENVIRONMENT is development.
    If production and ALLOWED_ORIGINS is '*', log warning and return empty list.
    """
    settings = get_settings()
    raw = (settings.ALLOWED_ORIGINS or "").strip()
    if not raw:
        return []
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    if settings.ENVIRONMENT == "development":
        return origins
    if "*" in origins:
        logger.warning(
            "ENVIRONMENT is production and ALLOWED_ORIGINS contains '*'; "
            "CORS wildcard not allowed in production"
        )
        return [o for o in origins if o != "*"]
    return origins


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every request: method, path, status code, duration ms."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s %s %.2fms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
