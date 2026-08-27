"""
Claude (Anthropic) LLM provider stub.

This is scaffolded for later implementation. The real provider requires
ANTHROPIC_API_KEY to be set.
"""

from typing import Optional, Sequence

from orca.schemas import LLMMessage


class ClaudeLLM:
    """Claude LLM provider (TODO: wire Anthropic SDK)."""

    def classify(self, text: str, labels: Sequence[str], *, system: Optional[str] = None) -> str:
        """Classify using Claude.

        TODO(orca): Implement via anthropic.Anthropic().messages.create()
        """
        raise NotImplementedError("Claude provider not yet wired; use ORCA_LLM_PROVIDER=mock")

    def narrate(self, facts: dict, *, system: str, max_words: int = 60) -> str:
        """Narrate using Claude.

        TODO(orca): Implement via anthropic.Anthropic().messages.create()
        """
        raise NotImplementedError("Claude provider not yet wired; use ORCA_LLM_PROVIDER=mock")

    def complete(self, messages: Sequence[LLMMessage], *, temperature: float = 0.0) -> str:
        """Complete using Claude.

        TODO(orca): Implement via anthropic.Anthropic().messages.create()
        """
        raise NotImplementedError("Claude provider not yet wired; use ORCA_LLM_PROVIDER=mock")
