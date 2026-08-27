"""
Factory for LLM provider selection.

Reads ORCA_LLM_PROVIDER env var and returns the appropriate implementation.
"""

from orca.config import settings
from orca.llm.base import LLMClient
from orca.llm.mock import MockLLM


def get_llm() -> LLMClient:
    """Get the LLM implementation based on config.

    Returns:
        An LLMClient implementation.

    Raises:
        ValueError: If the configured provider is not available.

    """
    provider = settings.llm_provider
    if provider == "mock":
        return MockLLM()
    elif provider == "claude":
        from orca.llm.claude import ClaudeLLM

        return ClaudeLLM()
    elif provider == "openai":
        from orca.llm.openai import OpenAILLM

        return OpenAILLM()
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
