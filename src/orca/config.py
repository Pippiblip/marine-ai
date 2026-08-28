"""
Configuration management for ORCA.

All settings are loaded from environment variables via Pydantic Settings.
Defaults provide safe, offline behavior (mock LLM, mock speech, mock data).
"""

from typing import Literal, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """ORCA configuration, loaded from .env or environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- AI Providers (all optional in MVP; defaults run fully offline) ---
    orca_llm_provider: Literal["mock", "claude", "openai"] = "mock"
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    orca_speech_provider: Literal["mock", "bhashini"] = "mock"
    bhashini_api_key: Optional[str] = None
    bhashini_user_id: Optional[str] = None

    # --- Data Mode ---
    orca_data_mode: Literal["mock", "real"] = "mock"

    # --- Infrastructure (optional in MVP) ---
    orca_redis_url: Optional[str] = None  # empty → use fakeredis
    orca_database_url: Optional[str] = None  # empty → in-memory/SQLite

    # --- Channels (only needed to run those channels live) ---
    whatsapp_token: Optional[str] = None
    whatsapp_phone_number_id: Optional[str] = None
    whatsapp_verify_token: Optional[str] = None
    # mock = in-process send log (tests/demo UI). live = Graph API to a real phone.
    orca_whatsapp_mode: Literal["mock", "live"] = "mock"
    exotel_sid: Optional[str] = None
    exotel_token: Optional[str] = None
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None

    # --- Guardrail Thresholds (defaults here; env vars override for demo) ---
    # SAFETY: these are the core go/no-go boundaries
    orca_wave_unsafe_m: float = 2.5
    orca_wind_unsafe_kt: float = 25.0
    orca_cyclone_near_km: float = 300.0
    orca_swell_unsafe_m: float = 2.0

    # --- Freshness Windows (in minutes/hours; converted to seconds in code) ---
    orca_freshness_max_min_safety: int = 30  # safety-relevant readings must be < 30 min old
    orca_freshness_max_hours_pfz: int = 6  # PFZ can be up to 6 hours old

    # --- Logging ---
    orca_log_level: str = "INFO"
    orca_trace_id_prefix: str = "orca"

    # --- API ---
    orca_api_host: str = "0.0.0.0"
    orca_api_port: int = 8000

    @property
    def llm_provider(self) -> Literal["mock", "claude", "openai"]:
        """LLM provider selection."""
        return self.orca_llm_provider

    @property
    def speech_provider(self) -> Literal["mock", "bhashini"]:
        """Speech provider selection."""
        return self.orca_speech_provider

    @property
    def data_mode(self) -> Literal["mock", "real"]:
        """Data source mode (mock fixtures or real APIs)."""
        return self.orca_data_mode

    @property
    def whatsapp_live(self) -> bool:
        """True when Cloud API send/receive should hit Meta (needs token + phone id)."""
        return (
            self.orca_whatsapp_mode == "live"
            and bool(self.whatsapp_token)
            and bool(self.whatsapp_phone_number_id)
        )

    @property
    def wave_unsafe_m(self) -> float:
        """Alias for ORCA safety threshold."""
        return self.orca_wave_unsafe_m

    @property
    def wind_unsafe_kt(self) -> float:
        """Alias for ORCA safety threshold."""
        return self.orca_wind_unsafe_kt

    @property
    def cyclone_near_km(self) -> float:
        """Alias for ORCA safety threshold."""
        return self.orca_cyclone_near_km

    @property
    def swell_unsafe_m(self) -> float:
        """Alias for ORCA safety threshold."""
        return self.orca_swell_unsafe_m

    @property
    def freshness_max_min_safety(self) -> int:
        """Alias for ORCA safety freshness window in minutes."""
        return self.orca_freshness_max_min_safety

    @property
    def freshness_max_hours_pfz(self) -> int:
        """Alias for ORCA PFZ freshness window in hours."""
        return self.orca_freshness_max_hours_pfz


# Singleton global settings instance
settings = Settings()  # type: ignore
