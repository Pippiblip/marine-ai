"""
Mock speech implementation (runs fully offline, deterministic).

This is the default implementation. Uses fixture transcripts and canned
audio so the pipeline works with zero API keys or keys.
"""


class MockSpeech:
    """Mock speech provider for offline development."""

    # Fixture transcripts (audio_id -> transcript)
    FIXTURE_TRANSCRIPTS = {
        "pfz_query_en": "Where is the nearest fishing zone today?",
        "pfz_query_ta": "இன்று அருகிலுள்ள மீன்பிடி மண்டலம் எங்கே?",
        "safety_query_en": "Is it safe to go out tomorrow morning?",
        "safety_query_ta": "நாளை காலையில் வெளியே செல்வது பாதுರக்ஷணமா?",
    }

    # Fixture language detections (text snippet -> lang)
    FIXTURE_LANG_DETECT = {
        "fishing zone": "en-IN",
        "safe": "en-IN",
        "அருகிலுள்ள": "ta-IN",
        "பாதுரக்ஷணமா": "ta-IN",
    }

    # Simple translations (lang pair, src snippet -> tgt snippet)
    FIXTURE_TRANSLATIONS = {
        ("ta-IN", "en-IN", "அருகிலுள்ள"): "nearest",
        ("ta-IN", "en-IN", "மீன்பிடி மண்டலம்"): "fishing zone",
    }

    # Canned WAV/MP3 audio (for testing; in real life, a file or bytes)
    CANNED_AUDIO = b"ID3\x04\x00\x00\x00\x00\x00\x00"  # minimal MP3 header

    def detect_language(self, audio: bytes) -> str:
        """Detect language from audio (mock).

        For testing: we'll detect based on audio content if it's a fixture,
        otherwise return "en-IN".
        """
        # In a mock, we can't really detect from audio bytes.
        # Return a default.
        return "en-IN"

    def asr(self, audio: bytes, lang: str) -> str:
        """ASR: audio → text (mock).

        Returns a fixture transcript. In production, would call Bhashini.
        """
        # Simple mock: return a default transcript
        # In real tests, we'd pass an audio_id or use a registry
        if lang.startswith("ta"):
            return self.FIXTURE_TRANSCRIPTS.get("pfz_query_ta", "மீன்பிடி மண்டலம் எங்கே?")
        return self.FIXTURE_TRANSCRIPTS.get("pfz_query_en", "Where is the nearest fishing zone?")

    def translate(self, text: str, src: str, tgt: str) -> str:
        """Translate text (mock).

        For testing: return the text unchanged (or a fixture translation).
        """
        # If target is English, we can do a simple passthrough or lookup
        if tgt == "en-IN" or tgt == "en-US":
            # Assume input is already English if src is also en-IN
            if src.startswith("en"):
                return text
            # Try fixture lookup (very limited)
            for (s, t, src_text), tgt_text in self.FIXTURE_TRANSLATIONS.items():
                if s == src and t == tgt and src_text in text:
                    return text.replace(src_text, tgt_text)
            # Fallback: return as-is (in real impl, would be translated)
            return text
        # Fallback: return unchanged
        return text

    def tts(self, text: str, lang: str) -> bytes:
        """TTS: text → audio (mock).

        Returns canned audio bytes. In production, would call Bhashini.
        """
        # Return a minimal valid MP3 header + silence
        return self.CANNED_AUDIO
