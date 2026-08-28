"""
Mock speech implementation (runs fully offline, deterministic).

This is the default implementation. Uses fixture transcripts and canned
audio so the pipeline works with zero API keys or keys.
"""

from pathlib import Path

_FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "speech"


class MockSpeech:
    """Mock speech provider for offline development."""

    FIXTURE_TRANSCRIPTS = {
        "pfz_query_en": "Where is the nearest fishing zone today?",
        "pfz_query_ta": "இன்று அருகிலுள்ள மீன்பிடி மண்டலம் எங்கே?",
        "safety_query_en": "Is it safe to go out tomorrow morning?",
        "safety_query_ta": "நாளை காலையில் வெளியே செல்வது பாதுகாப்பானதா?",
    }

    FIXTURE_LANG = {
        "pfz_query_en": "en-IN",
        "safety_query_en": "en-IN",
        "pfz_query_ta": "ta-IN",
        "safety_query_ta": "ta-IN",
    }

    CANNED_AUDIO = b"ID3\x04\x00\x00\x00\x00\x00\x00"

    def _audio_key(self, audio: bytes) -> str:
        try:
            key = audio.decode("utf-8")
        except UnicodeDecodeError:
            return ""
        return key if key in self.FIXTURE_TRANSCRIPTS else ""

    def detect_language(self, audio: bytes) -> str:
        """Detect language from a fixture audio id, else English."""
        key = self._audio_key(audio)
        if key:
            return self.FIXTURE_LANG[key]
        return "en-IN"

    def asr(self, audio: bytes, lang: str) -> str:
        """ASR: audio → text (mock)."""
        key = self._audio_key(audio)
        if key:
            return self.FIXTURE_TRANSCRIPTS[key]
        if lang.startswith("ta"):
            return self.FIXTURE_TRANSCRIPTS["pfz_query_ta"]
        return self.FIXTURE_TRANSCRIPTS["pfz_query_en"]

    def translate(self, text: str, src: str, tgt: str) -> str:
        """Translate text (mock). English passthrough; Tamil queries map to English."""
        if src.startswith("en") or tgt.startswith("en") and src.startswith("en"):
            if src.startswith("en"):
                return text
        if src.startswith("ta") and tgt.startswith("en"):
            if "மீன்பிடி" in text or "அருகிலுள்ள" in text:
                return "Where is the nearest fishing zone today?"
            if "பாதுகாப்பு" in text or "வெளியே" in text:
                return "Is it safe to go out tomorrow morning?"
        return text

    def tts(self, text: str, lang: str) -> bytes:
        """TTS: text → audio (mock)."""
        return self.CANNED_AUDIO + text.encode("utf-8")[:80]
