"""Outbound WhatsApp Cloud API adapter."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

import httpx
from pydantic import BaseModel

from orca.config import settings
from orca.schemas import SourceName, ToolResponse, ToolStatus
from orca.tools.base import ToolRequest, register

SENT_MESSAGES: list["WhatsAppSendRequest"] = []

GRAPH_URL = "https://graph.facebook.com/v21.0"


class WhatsAppSendRequest(ToolRequest):
    """Outbound WhatsApp message."""

    to: str
    text: str
    audio_bytes: Optional[bytes] = None
    audio_mime: str = "audio/mp4"


class WhatsAppSendPayload(BaseModel):
    """Record of a sent (or would-be-sent) message."""

    to: str
    text: str
    provider_message_id: str = "mock-wa-1"
    voice_note_id: Optional[str] = None


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.whatsapp_token}"}


def download_media(media_id: str) -> bytes | None:
    """Fetch inbound WhatsApp media bytes (voice notes). None if not live."""
    if not settings.whatsapp_live or not media_id:
        return None
    try:
        meta = httpx.get(f"{GRAPH_URL}/{media_id}", headers=_headers(), timeout=20.0)
        meta.raise_for_status()
        url = str(meta.json().get("url") or "")
        if not url:
            return None
        raw = httpx.get(url, headers=_headers(), timeout=30.0)
        raw.raise_for_status()
        return raw.content
    except httpx.HTTPError:
        return None


class WhatsAppSendMock:
    """Mock sender that records payloads for tests and the in-browser phone."""

    name = "whatsapp_send"
    source = SourceName.MOCK

    def __call__(self, req: WhatsAppSendRequest) -> ToolResponse:
        """Record the outbound message and return OK."""
        SENT_MESSAGES.append(req)
        return ToolResponse(
            status=ToolStatus.OK,
            source=self.source,
            retrieved_at=datetime.now(timezone.utc),
            payload=WhatsAppSendPayload(
                to=req.to,
                text=req.text,
                voice_note_id="mock-voice" if req.audio_bytes else None,
            ),
        )


class WhatsAppSendReal:
    """POST text and optional voice notes to WhatsApp Cloud API."""

    name = "whatsapp_send"
    source = SourceName.MOCK

    def _post_message(self, phone_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = httpx.post(
            f"{GRAPH_URL}/{phone_id}/messages",
            headers=_headers(),
            json=payload,
            timeout=20.0,
        )
        response.raise_for_status()
        return response.json()

    def _upload_audio(self, phone_id: str, audio: bytes, mime: str) -> str | None:
        """Upload a clip; return media id. Skip tiny mock TTS blobs."""
        if len(audio) < 256:
            return None
        files = {"file": ("orca-voice.m4a", audio, mime)}
        data = {"messaging_product": "whatsapp", "type": mime}
        response = httpx.post(
            f"{GRAPH_URL}/{phone_id}/media",
            headers=_headers(),
            data=data,
            files=files,
            timeout=30.0,
        )
        response.raise_for_status()
        return str(response.json().get("id") or "") or None

    def __call__(self, req: WhatsAppSendRequest) -> ToolResponse:
        """Send text, then a voice-note bubble when audio is real."""
        token = settings.whatsapp_token
        phone_id = settings.whatsapp_phone_number_id
        if not token or not phone_id:
            raise NotImplementedError(
                "TODO(orca): set WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID, ORCA_WHATSAPP_MODE=live"
            )
        to = req.to.lstrip("+")
        data = self._post_message(
            phone_id,
            {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": req.text[:4096], "preview_url": False},
            },
        )
        msg_id = "wa-live"
        try:
            msg_id = str(data["messages"][0]["id"])
        except (KeyError, IndexError, TypeError):
            pass
        voice_id = None
        if req.audio_bytes:
            # TODO(orca): if upload fails, text already went out — never invent a spoken number.
            try:
                media_id = self._upload_audio(phone_id, req.audio_bytes, req.audio_mime)
                if media_id:
                    self._post_message(
                        phone_id,
                        {
                            "messaging_product": "whatsapp",
                            "to": to,
                            "type": "audio",
                            "audio": {"id": media_id, "voice": True},
                        },
                    )
                    voice_id = media_id
            except httpx.HTTPError:
                voice_id = None
        SENT_MESSAGES.append(req)
        return ToolResponse(
            status=ToolStatus.OK,
            source=self.source,
            retrieved_at=datetime.now(timezone.utc),
            payload=WhatsAppSendPayload(
                to=req.to, text=req.text, provider_message_id=msg_id, voice_note_id=voice_id
            ),
        )


def clear_sent() -> None:
    """Reset the mock outbox (tests)."""
    SENT_MESSAGES.clear()


register(WhatsAppSendReal() if settings.whatsapp_live else WhatsAppSendMock())
