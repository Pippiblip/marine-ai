"""IVR / telephony inbound handler (Twilio-style form or JSON)."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Form, Request
from fastapi.responses import Response

from orca.graph import DEFAULT_LOCATION, run_query
from orca.tools.base import get_tool
from orca.tools.channels.ivr import IvrSpeakPayload, IvrSpeakRequest

router = APIRouter()


@router.post("/voice/inbound")
async def inbound_ivr(
    request: Request,
    SpeechResult: Optional[str] = Form(default=None),
    CallSid: Optional[str] = Form(default=None),
) -> Response:
    """Accept a simulated Twilio Voice webhook and return TwiML."""
    text = SpeechResult or ""
    call_sid = CallSid or "CA-mock"
    if request.headers.get("content-type", "").startswith("application/json"):
        body: dict[str, Any] = await request.json()
        text = str(body.get("SpeechResult") or body.get("text") or text)
        call_sid = str(body.get("CallSid") or body.get("call_sid") or call_sid)
        cell_id = str(body.get("cell_id") or "calm")
        force_error = bool(body.get("force_error", False))
        force_error_sources = list(body.get("force_error_sources") or [])
    else:
        cell_id = "calm"
        force_error = False
        force_error_sources = []
    state = run_query(
        text,
        user_location=DEFAULT_LOCATION,
        cell_id=cell_id,
        force_error=force_error,
        force_error_sources=force_error_sources,
        channel="ivr",
    )
    reply = state.get("final_response_text") or ""
    response = get_tool("ivr_speak")(
        IvrSpeakRequest(call_sid=call_sid, text=reply, lang=state.get("source_lang") or "en-IN")
    )
    payload = response.payload
    twiml = payload.twiml if isinstance(payload, IvrSpeakPayload) else f"<Say>{reply}</Say>"
    return Response(content=twiml, media_type="application/xml")
