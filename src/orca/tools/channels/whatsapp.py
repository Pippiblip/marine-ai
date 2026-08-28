"""Outbound WhatsApp Cloud API adapter."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

from orca.config import settings
from orca.schemas import SourceName, ToolResponse, ToolStatus
from orca.tools.base import ToolRequest, register

# Tests assert against this in-memory log; mock never hits the network.
SENT_MESSAGES: list["WhatsAppSendRequest"] = []


class WhatsAppSendRequest(ToolRequest):
    """Outbound WhatsApp message."""

    to: str
    text: str
    audio_bytes: Optional[bytes] = None


class WhatsAppSendPayload(BaseModel):
    """Record of a sent (or would-be-sent) message."""

    to: str
    text: str
    provider_message_id: str = "mock-wa-1"


class WhatsAppSendMock:
    """Mock sender that records payloads for tests."""

    name = "whatsapp_send"
    source = SourceName.MOCK

    def __call__(self, req: WhatsAppSendRequest) -> ToolResponse:
        """Record the outbound message and return OK."""
        SENT_MESSAGES.append(req)
        return ToolResponse(
            status=ToolStatus.OK,
            source=self.source,
            retrieved_at=datetime.now(timezone.utc),
            payload=WhatsAppSendPayload(to=req.to, text=req.text),
        )


class WhatsAppSendReal:
    """Real WhatsApp Cloud API adapter stub."""

    name = "whatsapp_send"
    source = SourceName.MOCK

    def __call__(self, req: WhatsAppSendRequest) -> ToolResponse:
        """Raise until Cloud API credentials are wired."""
        # TODO(orca): POST /messages with WHATSAPP_TOKEN; voice-note upload later.
        raise NotImplementedError("TODO(orca): wire WhatsApp Cloud API send")


def clear_sent() -> None:
    """Reset the mock outbox (tests)."""
    SENT_MESSAGES.clear()


register(WhatsAppSendReal() if settings.data_mode == "real" else WhatsAppSendMock())
