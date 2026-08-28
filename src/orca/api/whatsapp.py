"""WhatsApp Cloud API webhook (verify + inbound → graph → mock send)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from orca.config import settings
from orca.graph import DEFAULT_LOCATION, run_query
from orca.schemas import GeoPoint
from orca.tools.base import get_tool
from orca.tools.channels.whatsapp import WhatsAppSendRequest

router = APIRouter()

VERIFY_FALLBACK = "orca-dev"


@router.get("/webhooks/whatsapp")
async def verify_whatsapp(
    hub_mode: str = Query(default="", alias="hub.mode"),
    hub_verify_token: str = Query(default="", alias="hub.verify_token"),
    hub_challenge: str = Query(default="", alias="hub.challenge"),
) -> PlainTextResponse:
    """Meta webhook verification handshake."""
    expected = settings.whatsapp_verify_token or VERIFY_FALLBACK
    if hub_mode == "subscribe" and hub_verify_token == expected:
        return PlainTextResponse(hub_challenge)
    raise HTTPException(status_code=403, detail="verification failed")


def _extract_inbound(body: dict[str, Any]) -> tuple[str, str]:
    """Return (from_number, text) from a Cloud API-shaped payload."""
    try:
        value = body["entry"][0]["changes"][0]["value"]
        message = value["messages"][0]
        return str(message.get("from", "unknown")), str(message.get("text", {}).get("body", ""))
    except (KeyError, IndexError, TypeError):
        return str(body.get("from", "unknown")), str(body.get("text") or body.get("Body") or "")


@router.post("/webhooks/whatsapp")
async def inbound_whatsapp(request: Request) -> dict[str, Any]:
    """Run the graph on an inbound message and send via the mock adapter."""
    body = await request.json()
    sender, text = _extract_inbound(body)
    lat = body.get("lat")
    lon = body.get("lon")
    location = DEFAULT_LOCATION
    if lat is not None and lon is not None:
        location = GeoPoint(lat=float(lat), lon=float(lon))
    state = run_query(
        text,
        user_location=location,
        cell_id=str(body.get("cell_id") or "calm"),
        force_error=bool(body.get("force_error", False)),
        force_error_sources=list(body.get("force_error_sources") or []),
        channel="whatsapp",
    )
    reply = state.get("final_response_text") or ""
    get_tool("whatsapp_send")(WhatsAppSendRequest(to=sender, text=reply))
    return {"status": "ok", "to": sender, "text": reply}
