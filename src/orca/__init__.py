"""
ORCA — Marine EcOsystem Reasoning with Collaborative Agents.

A voice-first, multi-agent system that turns India's ocean and satellite data
into spoken, evidence-backed answers for coastal fishermen, over channels they
can afford: web push-to-talk, WhatsApp, and phone/IVR.

This is a Smart India Hackathon 2026 project for ISRO problem statement 26176.
"""

__version__ = "0.0.1"
__title__ = "ORCA"
__description__ = "Marine EcOsystem Reasoning with Collaborative Agents"

from orca.config import settings
from orca.logging import configure_logging, generate_trace_id, get_logger, get_trace_id

__all__ = [
    "settings",
    "configure_logging",
    "generate_trace_id",
    "get_trace_id",
    "get_logger",
]
