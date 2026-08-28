"""Turn a spoken reply into a WhatsApp-compatible audio clip when possible."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


def synthesize_voice_note(text: str, lang: str = "en-IN") -> bytes | None:
    """
    Build an M4A voice note for Cloud API upload.

    Uses macOS ``say`` + ``afconvert`` when present. Returns None on other
    platforms so the channel still sends text. Not used in offline tests.
    """
    spoken = (text or "").strip()
    if not spoken:
        return None
    if not shutil.which("say") or not shutil.which("afconvert"):
        return None
    voice = "Samantha"
    if lang.lower().startswith("hi"):
        voice = "Lekha"
    with tempfile.TemporaryDirectory() as tmp:
        aiff = Path(tmp) / "orca.aiff"
        m4a = Path(tmp) / "orca.m4a"
        try:
            subprocess.run(
                ["say", "-v", voice, "-o", str(aiff), spoken[:800]],
                check=True,
                capture_output=True,
                timeout=30,
            )
            subprocess.run(
                ["afconvert", "-f", "m4af", "-d", "aac", str(aiff), str(m4a)],
                check=True,
                capture_output=True,
                timeout=30,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
            return None
        if not m4a.exists():
            return None
        return m4a.read_bytes()
