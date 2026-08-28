"""WhatsApp Cloud API webhook (verify + inbound → graph → send)."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from orca.config import settings
from orca.graph import DEFAULT_LOCATION, run_query
from orca.logging import get_logger
from orca.schemas import GeoPoint
from orca.speech.factory import get_speech
from orca.speech.voice_note import synthesize_voice_note
from orca.tools.base import get_tool
from orca.tools.channels.whatsapp import WhatsAppSendPayload, WhatsAppSendRequest, download_media

router = APIRouter()
logger = get_logger(__name__)

VERIFY_FALLBACK = "orca-dev"

_TYPE_PLEASE = (
    "I received a voice note, but live speech-to-text is not enabled. "
    "Please type your question (for example: Where is the nearest fishing zone?). "
    "Share your location pin so I can use your GPS. "
    "Add the word cyclone to use the storm fixture, or kill weather to demo a dead source."
)


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


def _message_block(body: dict[str, Any]) -> dict[str, Any]:
    try:
        return dict(body["entry"][0]["changes"][0]["value"]["messages"][0])
    except (KeyError, IndexError, TypeError):
        return {}


def _is_status_only(body: dict[str, Any]) -> bool:
    try:
        value = body["entry"][0]["changes"][0]["value"]
    except (KeyError, IndexError, TypeError):
        return False
    return bool(value.get("statuses")) and not value.get("messages")


def _switches_from_text(text: str, demo: dict[str, Any]) -> tuple[str, list[str]]:
    """Phone users have no dropdown — keywords pick the demo cell / kill switch."""
    cell = str(demo.get("cell_id") or "calm")
    kills = list(demo.get("force_error_sources") or [])
    lower = text.lower()
    if "cyclone" in lower or "storm" in lower:
        cell = "cyclone"
    if "kill weather" in lower or lower.startswith("/kill"):
        kills = ["imd_marine"]
        cell = "cyclone"
    return cell, kills


def _extract_inbound(body: dict[str, Any]) -> tuple[str, str, Optional[GeoPoint], Optional[str]]:
    """Parse Cloud API JSON: sender, text, GPS pin, inbound audio media id."""
    message = _message_block(body)
    sender = str(message.get("from") or body.get("from") or "unknown")
    text = ""
    if isinstance(message.get("text"), dict):
        text = str(message["text"].get("body") or "")
    elif body.get("text"):
        text = str(body.get("text") or body.get("Body") or "")
    loc: Optional[GeoPoint] = None
    pin = message.get("location") if isinstance(message.get("location"), dict) else None
    if pin and pin.get("latitude") is not None and pin.get("longitude") is not None:
        loc = GeoPoint(lat=float(pin["latitude"]), lon=float(pin["longitude"]))
        if not text:
            text = "Is it safe to go out from here?"
    if loc is None and body.get("lat") is not None and body.get("lon") is not None:
        loc = GeoPoint(lat=float(body["lat"]), lon=float(body["lon"]))
    media_id: Optional[str] = None
    audio = message.get("audio") if isinstance(message.get("audio"), dict) else None
    if audio and audio.get("id"):
        media_id = str(audio["id"])
    voice = message.get("voice") if isinstance(message.get("voice"), dict) else None
    if voice and voice.get("id"):
        media_id = str(voice["id"])
    return sender, text, loc, media_id


@router.post("/webhooks/whatsapp")
async def inbound_whatsapp(request: Request) -> dict[str, Any]:
    """Run the graph on an inbound WhatsApp message and send the reply."""
    body = await request.json()
    if _is_status_only(body):
        return {"status": "ignored"}

    sender, text, pin, media_id = _extract_inbound(body)
    demo = body.get("orca") if isinstance(body.get("orca"), dict) else {}
    audio_id = str(demo["audio_id"]) if demo.get("audio_id") else None
    source_lang = str(demo.get("source_lang") or "en-IN")

    if media_id and not text and not audio_id:
        if settings.speech_provider != "mock" and settings.whatsapp_live:
            clip = download_media(media_id)
            if clip:
                speech = get_speech()
                source_lang = speech.detect_language(clip)
                native = speech.asr(clip, source_lang)
                text = speech.translate(native, source_lang, "en-IN")
        if not text:
            get_tool("whatsapp_send")(WhatsAppSendRequest(to=sender, text=_TYPE_PLEASE))
            return {"status": "ok", "to": sender, "text": _TYPE_PLEASE, "channel": "whatsapp"}

    if not (text or audio_id or pin):
        return {"status": "ignored"}

    cell_id, kills = _switches_from_text(text, demo)
    location = pin or DEFAULT_LOCATION
    if demo.get("has_location") is False:
        location = None
    state = run_query(
        text,
        audio_id=audio_id,
        user_location=location,
        cell_id=cell_id,
        force_error=bool(demo.get("force_error") or body.get("force_error", False)),
        force_error_sources=kills,
        source_lang=source_lang,
        channel="whatsapp",
    )
    reply = state.get("response_lang_text") or state.get("final_response_text") or ""
    voice = synthesize_voice_note(reply, source_lang) if settings.whatsapp_live else get_speech().tts(reply, source_lang)
    sent = get_tool("whatsapp_send")(
        WhatsAppSendRequest(
            to=sender,
            text=reply,
            audio_bytes=voice,
            audio_mime="audio/mp4",
        )
    )
    payload = sent.payload
    voice_id = payload.voice_note_id if isinstance(payload, WhatsAppSendPayload) else None
    logger.info("whatsapp reply queued", extra={"extra_fields": {"to": sender}})
    return {
        "status": "ok",
        "to": sender,
        "text": reply,
        "intent": state.get("intent"),
        "guardrail_status": state.get("guardrail_status"),
        "citations": state.get("citations") or [],
        "channel": "whatsapp",
        "via": "whatsapp_send",
        "voice_note": bool(voice_id or voice),
    }
