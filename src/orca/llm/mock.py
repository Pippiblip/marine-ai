"""
Mock LLM implementation (runs fully offline, deterministic).

This is the default implementation. Uses keyword-based classification
and template narration so it works with zero API keys.
"""

from typing import Dict, Optional, Sequence

from orca.schemas import LLMMessage


class MockLLM:
    """Mock LLM for offline development and testing."""

    # Intent classification rules (keyword -> label)
    INTENT_KEYWORDS = {
        "fishing zone": "pfz_nearest",
        "nearest": "pfz_nearest",
        "where": "pfz_nearest",
        "safe": "safety_check",
        "go out": "safety_check",
        "dangerous": "safety_check",
        "boundary": "boundary_check",
        "imbl": "boundary_check",
    }

    # Narration templates for common fact patterns
    NARRATION_TEMPLATES = {
        "zone_info": "The nearest fishing zone is about {distance} km to the {bearing}. "
        "Depth around {depth} m, waters look {condition}.",
        "safety_clear": "Conditions look safe: waves {wave} m, wind {wind} kt. "
        "Always stay alert.",
        "safety_unsafe": "Do not go out. Wave height {wave} m, wind {wind} kt, "
        "above safe limits.",
        "fallback": "Based on available data: {summary}.",
    }

    def classify(self, text: str, labels: Sequence[str], *, system: Optional[str] = None) -> str:
        """Classify by keyword matching.

        Falls back to the first label if no keywords match.
        """
        text_lower = text.lower()
        for keyword, intent in self.INTENT_KEYWORDS.items():
            if keyword in text_lower:
                # Return this intent if it's in the allowed labels
                if intent in labels:
                    return intent
        # Fallback: return first label in the sequence
        return labels[0] if labels else "unknown"

    def narrate(self, facts: Dict, *, system: str, max_words: int = 60) -> str:
        """Narrate facts using template matching.

        Returns a plain sentence built from the facts dict.
        """
        # Simple template-based narration
        if "zone_name" in facts:
            return self.NARRATION_TEMPLATES["zone_info"].format(**facts)
        if "wave_height" in facts and "wind_speed" in facts:
            wave = facts.get("wave_height", "unknown")
            wind = facts.get("wind_speed", "unknown")
            if wave and wind:
                try:
                    if float(wave) > 2.5 or float(wind) > 25:
                        return f"Do not go out. Waves {wave} m, wind {wind} kt."
                    return f"Safe conditions: waves {wave} m, wind {wind} kt."
                except (ValueError, TypeError):
                    pass
        # Fallback
        summary = ", ".join([f"{k}: {v}" for k, v in facts.items()])
        return self.NARRATION_TEMPLATES["fallback"].format(summary=summary)

    def complete(self, messages: Sequence[LLMMessage], *, temperature: float = 0.0) -> str:
        """Complete by echoing back context or a canned response."""
        if not messages:
            return "No context provided."
        last_msg = messages[-1]
        # Very simple: if the last message looks like a question, give a neutral response
        if last_msg.role == "user":
            if "?" in last_msg.content:
                return "I don't have enough information to answer that with confidence."
            return f"Understood: {last_msg.content[:50]}..."
        return "OK."
