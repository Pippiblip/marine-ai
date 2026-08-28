"""FastAPI application for ORCA."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import orca.tools  # noqa: F401  # register adapters
from orca import __title__, __version__
from orca.api import ivr, whatsapp, ws
from orca.api.serialize import query_view
from orca.config import settings
from orca.graph import DEFAULT_LOCATION, run_query
from orca.guardrails.resilience import fetch
from orca.logging import get_logger
from orca.schemas import GeoPoint, ToolResponse
from orca.speech.factory import get_speech
from orca.tools.base import get_tool
from orca.tools.imd import MarineWarningRequest
from orca.tools.incois import PFZRequest
from orca.tools.isro import ChlorophyllRequest

logger = get_logger(__name__)

WEB_DIR = Path(__file__).resolve().parents[3] / "clients" / "web"


class QueryRequest(BaseModel):
    """Text or mock-audio query from the web client."""

    text: str = ""
    audio_id: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    has_location: bool = True
    cell_id: str = "calm"
    force_error: bool = False
    force_error_sources: list[str] = Field(default_factory=list)
    source_lang: str = "en-IN"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Handle startup and shutdown events."""
    logger.info(f"{__title__} v{__version__} started")
    yield
    logger.info(f"{__title__} shutting down")


app = FastAPI(
    title=__title__,
    version=__version__,
    description="Marine EcOsystem Reasoning with Collaborative Agents",
    lifespan=lifespan,
)
app.include_router(ws.router)
app.include_router(whatsapp.router)
app.include_router(ivr.router)

if WEB_DIR.exists():
    app.mount("/assets", StaticFiles(directory=WEB_DIR), name="assets")


@app.get("/")
async def home() -> FileResponse:
    """Serve the push-to-talk web client."""
    index = WEB_DIR / "index.html"
    if not index.exists():
        raise HTTPException(status_code=404, detail="web client missing")
    return FileResponse(index, headers={"Cache-Control": "no-store"})


@app.get("/whatsapp/connect")
async def whatsapp_connect() -> FileResponse:
    """How to point a real phone at this instance (Meta Cloud API + HTTPS)."""
    page = WEB_DIR / "connect-whatsapp.html"
    if not page.exists():
        raise HTTPException(status_code=404, detail="connect page missing")
    return FileResponse(page, headers={"Cache-Control": "no-store"})


@app.get("/whatsapp")
async def whatsapp_client() -> FileResponse:
    """Serve the in-browser WhatsApp channel (same webhook as Cloud API)."""
    page = WEB_DIR / "whatsapp.html"
    if not page.exists():
        raise HTTPException(status_code=404, detail="whatsapp client missing")
    return FileResponse(page, headers={"Cache-Control": "no-store"})


@app.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse(
        {"status": "ok", "version": __version__, "data_mode": settings.data_mode}
    )


@app.post("/api/query")
async def api_query(body: QueryRequest) -> JSONResponse:
    """Run one graph query and return the spoken text plus citations."""
    location: Optional[GeoPoint]
    if not body.has_location:
        location = None
    elif body.lat is not None and body.lon is not None:
        location = GeoPoint(lat=body.lat, lon=body.lon)
    else:
        location = DEFAULT_LOCATION
    state = run_query(
        body.text,
        audio_id=body.audio_id,
        user_location=location,
        cell_id=body.cell_id,
        force_error=body.force_error,
        force_error_sources=body.force_error_sources,
        source_lang=body.source_lang,
        channel="web",
    )
    text = state.get("final_response_text") or ""
    audio = get_speech().tts(text, body.source_lang)
    payload = {
        "text": text,
        "response_lang_text": state.get("response_lang_text"),
        "citations": state.get("citations") or [],
        "guardrail_status": state.get("guardrail_status"),
        "intent": state.get("intent"),
        "trace_id": state.get("trace_id"),
        "audio_bytes": len(audio),
    }
    payload.update(query_view(state))
    return JSONResponse(payload)


@app.get("/api/tools/{tool_name}")
async def run_tool(
    tool_name: str,
    cell_id: str = Query(default="calm"),
    force_error: bool = Query(default=False),
) -> JSONResponse:
    """Run one registered fixture tool through the resilience layer."""
    requests: dict[str, Any] = {
        "incois_get_pfz": PFZRequest(cell_id=cell_id, force_error=force_error),
        "imd_get_marine_warnings": MarineWarningRequest(cell_id=cell_id, force_error=force_error),
        "isro_get_chlorophyll": ChlorophyllRequest(cell_id=cell_id, force_error=force_error),
    }
    if tool_name not in requests:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")
    tool = get_tool(tool_name)
    response: ToolResponse = fetch(tool, requests[tool_name], tool.source)
    return JSONResponse(response.model_dump(mode="json"))
