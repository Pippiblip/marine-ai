"""
Factory for speech provider selection.

Reads ORCA_SPEECH_PROVIDER env var and returns the appropriate implementation.
"""

from orca.config import settings
from orca.speech.base import SpeechClient
from orca.speech.mock import MockSpeech


def get_speech() -> SpeechClient:
    """Get the speech implementation based on config.

    Returns:
        A SpeechClient implementation.

    Raises:
        ValueError: If the configured provider is not available.

    """
    provider = settings.speech_provider
    if provider == "mock":
        return MockSpeech()
    elif provider == "bhashini":
        from orca.speech.bhashini import BhashiniSpeech

        return BhashiniSpeech()
    else:
        raise ValueError(f"Unknown speech provider: {provider}")
