"""
Mock LLM implementation (runs fully offline, deterministic).

This is the default implementation. Uses keyword-based classification
and template narration so it works with zero API keys.
"""

from typing import Dict, Optional, Sequence

from orca.schemas import LLMMessage


class MockLLM:
    """Mock LLM for offline development and testing."""

    def classify(self, text: str, labels: Sequence[str], *, system: Optional[str] = None) -> str:
        """Classify by keyword matching.

        Falls back to the first label if no keywords match.
        """
        text_lower = text.lower()
        ranked = [
            (("safe", "go out", "dangerous", "cyclone", "storm", "weather"), "safety_check"),
            (("fishing zone", "fishing", "pfz", "catch", "nearest"), "pfz_nearest"),
            (("boundary", "imbl", "border", "maritime line"), "boundary_check"),
        ]
        for keywords, intent in ranked:
            if any(keyword in text_lower for keyword in keywords) and intent in labels:
                return intent
        return labels[0] if labels else "unknown"

    def narrate(self, facts: Dict, *, system: str, max_words: int = 60) -> str:
        """Narrate facts using templates. Never invents numbers not in facts."""
        if "zone_name" in facts:
            return (
                f"The nearest fishing zone is about {facts['distance']} km "
                f"to the {facts['bearing']}. Depth around {facts.get('depth', 'unknown')} m, "
                f"waters look {facts.get('condition', 'productive')}."
            )
        summary = ", ".join([f"{k}: {v}" for k, v in facts.items()])
        return f"Based on available data: {summary}."

    def complete(self, messages: Sequence[LLMMessage], *, temperature: float = 0.0) -> str:
        """Complete by echoing back context or a canned response."""
        if not messages:
            return "No context provided."
        last_msg = messages[-1]
        if last_msg.role == "user":
            if "?" in last_msg.content:
                return "I don't have enough information to answer that with confidence."
            return f"Understood: {last_msg.content[:50]}..."
        return "OK."
