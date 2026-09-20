from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from jarvis.api.routes import connectors, health, livekit, profile
from jarvis.config import PROJECT_ROOT, get_settings

load_dotenv(PROJECT_ROOT / ".env.local")

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    )
    logger.info("Jarvis API starting")
    yield
    logger.info("Jarvis API stopping")


def create_app() -> FastAPI:
    """App factory - lets tests build an isolated app instance."""
    settings = get_settings()
    app = FastAPI(title="Jarvis API", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api")
    app.include_router(livekit.router, prefix="/api")
    app.include_router(connectors.router, prefix="/api")
    app.include_router(profile.router, prefix="/api")
    return app


app = create_app()