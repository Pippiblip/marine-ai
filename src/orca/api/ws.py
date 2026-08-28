"""WebSocket push-to-talk endpoint."""

from __future__ import annotations

import base64
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from orca.graph import DEFAULT_LOCATION, run_query
from orca.logging import get_logger
from orca.schemas import GeoPoint
from orca.speech.factory import get_speech

logger = get_logger(__name__)
router = APIRouter()


def _location(payload: dict[str, Any]) -> GeoPoint | None:
    if payload.get("lat") is None or payload.get("lon") is None:
        return DEFAULT_LOCATION
    return GeoPoint(lat=float(payload["lat"]), lon=float(payload["lon"]))


@router.websocket("/ws")
async def push_to_talk(websocket: WebSocket) -> None:
    """Accept JSON frames, run the graph, return text + mock audio."""
    await websocket.accept()
    speech = get_speech()
    try:
        while True:
            payload = await websocket.receive_json()
            location = _location(payload)
            if payload.get("has_location") is False:
                location = None
            state = run_query(
                payload.get("text") or "",
                audio_id=payload.get("audio_id"),
                user_location=location,
                cell_id=payload.get("cell_id") or "calm",
                force_error=bool(payload.get("force_error", False)),
                force_error_sources=list(payload.get("force_error_sources") or []),
                source_lang=payload.get("source_lang") or "en-IN",
                channel="web",
            )
            text = state.get("response_lang_text") or state.get("final_response_text") or ""
            audio = speech.tts(text, state.get("source_lang") or "en-IN")
            await websocket.send_json(
                {
                    "text": text,
                    "citations": state.get("citations") or [],
                    "guardrail_status": state.get("guardrail_status"),
                    "intent": state.get("intent"),
                    "audio_b64": base64.b64encode(audio).decode("ascii"),
                    "trace_id": state.get("trace_id"),
                }
            )
    except WebSocketDisconnect:
        logger.info("websocket disconnected")
