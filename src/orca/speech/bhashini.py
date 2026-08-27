"""
Bhashini speech provider stub.

This is scaffolded for later implementation. The real provider requires
BHASHINI_API_KEY and BHASHINI_USER_ID to be set.

Bhashini (AI4Bharat) provides open-source ASR, TTS, and translation for
Indian languages via the ULCA pipeline.
"""


class BhashiniSpeech:
    """Bhashini speech provider (TODO: wire ULCA pipeline)."""

    def detect_language(self, audio: bytes) -> str:
        """Detect language via Bhashini.

        TODO(orca): Call ULCA language identification endpoint.
        """
        raise NotImplementedError("Bhashini provider not yet wired; use ORCA_SPEECH_PROVIDER=mock")

    def asr(self, audio: bytes, lang: str) -> str:
        """ASR via Bhashini.

        TODO(orca): Call ULCA streaming ASR endpoint (preferably for low-latency).
        """
        raise NotImplementedError("Bhashini provider not yet wired; use ORCA_SPEECH_PROVIDER=mock")

    def translate(self, text: str, src: str, tgt: str) -> str:
        """Translate via Bhashini IndicTrans2.

        TODO(orca): Call ULCA translation endpoint. IndicTrans2 covers
        regional Indian languages ↔ English.
        """
        raise NotImplementedError("Bhashini provider not yet wired; use ORCA_SPEECH_PROVIDER=mock")

    def tts(self, text: str, lang: str) -> bytes:
        """TTS via Bhashini Indic-TTS or Kokoro.

        TODO(orca): Call ULCA TTS endpoint, stream audio chunks back.
        """
        raise NotImplementedError("Bhashini provider not yet wired; use ORCA_SPEECH_PROVIDER=mock")
