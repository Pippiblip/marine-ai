"""Outbound IVR / telephony speak adapter."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel

from orca.config import settings
from orca.schemas import SourceName, ToolResponse, ToolStatus
from orca.tools.base import ToolRequest, register

SPOKEN: list["IvrSpeakRequest"] = []


class IvrSpeakRequest(ToolRequest):
    """Ask the telephony provider to speak a reply."""

    call_sid: str
    text: str
    audio_bytes: Optional[bytes] = None
    lang: str = "en-IN"


class IvrSpeakPayload(BaseModel):
    """Would-be TwiML / Exotel response."""

    twiml: str
    call_sid: str


class IvrSpeakMock:
    """Mock IVR that records TwiML for tests."""

    name = "ivr_speak"
    source = SourceName.MOCK

    def __call__(self, req: IvrSpeakRequest) -> ToolResponse:
        """Build a Say TwiML document without placing a real call."""
        twiml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            f"<Response><Say>{req.text}</Say></Response>"
        )
        SPOKEN.append(req)
        return ToolResponse(
            status=ToolStatus.OK,
            source=self.source,
            retrieved_at=datetime.now(timezone.utc),
            payload=IvrSpeakPayload(twiml=twiml, call_sid=req.call_sid),
        )


class IvrSpeakReal:
    """Real Exotel/Twilio speak adapter stub."""

    name = "ivr_speak"
    source = SourceName.MOCK

    def __call__(self, req: IvrSpeakRequest) -> ToolResponse:
        """Raise until telephony credentials are wired."""
        # TODO(orca): fill Exotel/Twilio media + TTS specifics.
        raise NotImplementedError("TODO(orca): wire Exotel/Twilio IVR speak")


def clear_spoken() -> None:
    """Reset the mock IVR log (tests)."""
    SPOKEN.clear()


register(IvrSpeakReal() if settings.data_mode == "real" else IvrSpeakMock())
