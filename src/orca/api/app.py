"""FastAPI application for ORCA."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from orca import __title__, __version__

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Handle startup and shutdown events."""
    logger.info(f"{__title__} v{__version__} started")
    yield
    logger.info(f"{__title__} shutting down")


# Create FastAPI app
app = FastAPI(
    title=__title__,
    version=__version__,
    description="Marine EcOsystem Reasoning with Collaborative Agents",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse({"status": "ok", "version": __version__})
