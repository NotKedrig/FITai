from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings


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
    return app


app = create_app()

