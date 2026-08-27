"""
OpenAI LLM provider stub.

This is scaffolded for later implementation. The real provider requires
OPENAI_API_KEY to be set.
"""

from typing import Optional, Sequence

from orca.schemas import LLMMessage


class OpenAILLM:
    """OpenAI LLM provider (TODO: wire OpenAI SDK)."""

    def classify(self, text: str, labels: Sequence[str], *, system: Optional[str] = None) -> str:
        """Classify using OpenAI.

        TODO(orca): Implement via openai.OpenAI().chat.completions.create()
        """
        raise NotImplementedError("OpenAI provider not yet wired; use ORCA_LLM_PROVIDER=mock")

    def narrate(self, facts: dict, *, system: str, max_words: int = 60) -> str:
        """Narrate using OpenAI.

        TODO(orca): Implement via openai.OpenAI().chat.completions.create()
        """
        raise NotImplementedError("OpenAI provider not yet wired; use ORCA_LLM_PROVIDER=mock")

    def complete(self, messages: Sequence[LLMMessage], *, temperature: float = 0.0) -> str:
        """Complete using OpenAI.

        TODO(orca): Implement via openai.OpenAI().chat.completions.create()
        """
        raise NotImplementedError("OpenAI provider not yet wired; use ORCA_LLM_PROVIDER=mock")
