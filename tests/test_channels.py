"""WhatsApp and IVR routes round-trip through the mock channel adapters."""

from fastapi.testclient import TestClient

from orca.api.app import app
from orca.tools.channels import ivr as ivr_mod
from orca.tools.channels import whatsapp as wa_mod


def test_whatsapp_verify():
    """Webhook verification echoes the challenge when the token matches."""
    client = TestClient(app)
    response = client.get(
        "/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "orca-dev",
            "hub.challenge": "abc123",
        },
    )
    assert response.status_code == 200
    assert response.text == "abc123"


def test_whatsapp_inbound_sends_via_mock():
    """An inbound WhatsApp payload produces an outbound mock send."""
    wa_mod.clear_sent()
    client = TestClient(app)
    response = client.post(
        "/webhooks/whatsapp",
        json={
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "9198",
                                        "text": {"body": "Where is the nearest fishing zone?"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        },
    )
    assert response.status_code == 200
    assert wa_mod.SENT_MESSAGES
    assert response.json()["channel"] == "whatsapp"
    assert "km" in wa_mod.SENT_MESSAGES[-1].text or "fishing" in wa_mod.SENT_MESSAGES[-1].text.lower()
    assert "citations" in response.json()


def test_whatsapp_location_pin_is_accepted():
    """A Cloud API location message is treated as the user's GPS."""
    wa_mod.clear_sent()
    client = TestClient(app)
    response = client.post(
        "/webhooks/whatsapp",
        json={
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "9198",
                                        "type": "location",
                                        "location": {"latitude": 12.42, "longitude": 79.40},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ],
            "orca": {"cell_id": "cyclone"},
        },
    )
    assert response.status_code == 200
    assert "Do not go out" in response.json()["text"] or "won't guess" in response.json()["text"]


def test_whatsapp_page_renders():
    """The phone UI should be served for the hall demo."""
    page = TestClient(app).get("/whatsapp")
    assert page.status_code == 200
    assert "WhatsApp" in page.text
    assert "/webhooks/whatsapp" in page.text
    assert "Kill weather" in page.text


def test_whatsapp_connect_page_explains_phone_setup():
    """Setup copy must tell operators to use the real WhatsApp app."""
    page = TestClient(app).get("/whatsapp/connect")
    assert page.status_code == 200
    assert "ngrok" in page.text
    assert "ORCA_WHATSAPP_MODE" in page.text


def test_whatsapp_tamil_audio_id_round_trips():
    """Demo Tamil chip uses the same ASR fixture as the voice client."""
    wa_mod.clear_sent()
    response = TestClient(app).post(
        "/webhooks/whatsapp",
        json={
            "from": "9198",
            "text": "",
            "orca": {"audio_id": "pfz_query_ta", "source_lang": "ta-IN", "cell_id": "calm"},
        },
    )
    assert response.status_code == 200
    assert response.json()["intent"] == "pfz_nearest"


def test_whatsapp_ignores_delivery_status():
    """Meta status callbacks must not run the graph."""
    wa_mod.clear_sent()
    response = TestClient(app).post(
        "/webhooks/whatsapp",
        json={"entry": [{"changes": [{"value": {"statuses": [{"status": "delivered"}]}}]}]},
    )
    assert response.json()["status"] == "ignored"
    assert wa_mod.SENT_MESSAGES == []


def test_whatsapp_cyclone_keyword_without_dropdown():
    """Phone users select the storm fixture by saying cyclone in the text."""
    wa_mod.clear_sent()
    response = TestClient(app).post(
        "/webhooks/whatsapp",
        json={
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "9198",
                                        "text": {"body": "Is it safe to go out? cyclone"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        },
    )
    assert "Do not go out" in response.json()["text"]
    assert response.json().get("voice_note") is True


def test_ivr_inbound_returns_twiml():
    """A simulated Twilio voice webhook returns TwiML from the mock IVR tool."""
    ivr_mod.clear_spoken()
    client = TestClient(app)
    response = client.post(
        "/voice/inbound",
        json={"SpeechResult": "Where is the nearest fishing zone?", "CallSid": "CA1"},
    )
    assert response.status_code == 200
    assert "Say" in response.text
    assert ivr_mod.SPOKEN
