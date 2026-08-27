"""
Speech provider interface (protocol).

Handles ASR (speech-to-text), language detection, translation, and TTS
(text-to-speech). All implementations satisfy this interface.
"""

from typing import Protocol


class SpeechClient(Protocol):
    """Interface for speech operations. All implementations satisfy this."""

    def detect_language(self, audio: bytes) -> str:
        """Detect the language of audio.

        Args:
            audio: Raw audio bytes.

        Returns:
            BCP 47 language code (e.g., "ta-IN", "en-US").

        """
        ...

    def asr(self, audio: bytes, lang: str) -> str:
        """Automatic speech recognition: audio → text.

        Args:
            audio: Raw audio bytes.
            lang: BCP 47 language code.

        Returns:
            Transcribed text.

        """
        ...

    def translate(self, text: str, src: str, tgt: str) -> str:
        """Translate text from source to target language.

        Args:
            text: Text to translate.
            src: Source language (BCP 47).
            tgt: Target language (BCP 47).

        Returns:
            Translated text.

        """
        ...

    def tts(self, text: str, lang: str) -> bytes:
        """Text-to-speech: text → audio.

        Args:
            text: Text to synthesize.
            lang: BCP 47 language code.

        Returns:
            Raw audio bytes (WAV or MP3).

        """
        ...
