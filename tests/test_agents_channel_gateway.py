"""Channel gateway normalizes audio and text into English query state."""

from orca.agents.channel_gateway import channel_gateway_node


def test_typed_english_passthrough():
    """Typed English is stored as query_text without inventing a location."""
    out = channel_gateway_node(
        {
            "query_text": "Where is the nearest fishing zone?",
            "source_lang": "en-IN",
            "channel": "web",
        }
    )
    assert out["query_text"] == "Where is the nearest fishing zone?"
    assert out["source_lang"] == "en-IN"
    assert out["user_location"] is None
    assert out["trace_id"]


def test_tamil_audio_id_translates_to_english():
    """A fixture Tamil audio id becomes an English fishing-zone query."""
    out = channel_gateway_node({"audio_id": "pfz_query_ta", "channel": "web"})
    assert out["source_lang"] == "ta-IN"
    assert "fishing zone" in out["query_text"].lower()
