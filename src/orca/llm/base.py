"""
LLM provider interface (protocol).

All agents use this interface; they never import vendor SDKs directly.
Implementations are selected by config at runtime.
"""

from typing import Optional, Protocol, Sequence

from orca.schemas import LLMMessage


class LLMClient(Protocol):
    """Interface for LLM operations. All implementations satisfy this."""

    def classify(self, text: str, labels: Sequence[str], *, system: Optional[str] = None) -> str:
        """
        Classify text into exactly one label from the given set.

        Used by the Router for intent classification. Must be deterministic
        and never return a label not in the given set.

        Args:
            text: The text to classify.
            labels: Allowed labels (exact options).
            system: Optional system prompt for context.

        Returns:
            Exactly one label from `labels`.

        """
        ...

    def narrate(self, facts: dict, *, system: str, max_words: int = 60) -> str:
        """
        Turn already-retrieved facts into ONE plain sentence.

        MUST NOT add numbers not in `facts`. Used by Synthesis to narrate
        retrieved data into user-facing language.

        Args:
            facts: Dict of fact_key -> value that came from retrieved data.
            system: System prompt defining the narration style.
            max_words: Target word count (soft limit).

        Returns:
            A single sentence narrating the facts.

        """
        ...

    def complete(self, messages: Sequence[LLMMessage], *, temperature: float = 0.0) -> str:
        """
        Complete a conversation.

        Args:
            messages: Sequence of LLMMessage objects (role + content).
            temperature: Sampling temperature (0.0 = deterministic).

        Returns:
            The model's response text.

        """
        ...
