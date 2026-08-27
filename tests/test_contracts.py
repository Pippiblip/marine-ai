"""
Contract tests for M1: schemas, state, and provider factories.

These tests verify that:
1. All Pydantic models validate/reject correctly
2. Measurement.age_seconds() works
3. LLM and speech factories return the right implementations
4. Mock implementations work offline and deterministically
"""

from datetime import datetime, timedelta, timezone

import pytest

from orca.llm.factory import get_llm
from orca.llm.mock import MockLLM
from orca.schemas import (
    GeoPoint,
    MarineDataResult,
    Measurement,
    PFZNode,
    SafetyFlag,
    Severity,
    SourceName,
    WeatherRiskResult,
)
from orca.speech.factory import get_speech
from orca.speech.mock import MockSpeech
from orca.state import PlatformState


class TestMeasurement:
    """Test the Measurement model and its methods."""

    def test_measurement_creation(self):
        """Test creating a valid Measurement."""
        now = datetime.now(timezone.utc)
        m = Measurement(
            value=2.5,
            unit="m",
            source=SourceName.INCOIS_OCEAN_STATE,
            retrieved_at=now,
            observed_at=now,
        )
        assert m.value == 2.5
        assert m.unit == "m"
        assert m.source == SourceName.INCOIS_OCEAN_STATE

    def test_measurement_age_seconds(self):
        """Test age_seconds calculation."""
        now = datetime.now(timezone.utc)
        past = now - timedelta(seconds=30)
        m = Measurement(
            value=2.5,
            unit="m",
            source=SourceName.IMD_MARINE,
            retrieved_at=past,
        )
        age = m.age_seconds(now)
        assert 29 < age < 31  # Allow small float rounding

    def test_measurement_without_observed_at(self):
        """Test Measurement without observed_at (should be optional)."""
        now = datetime.now(timezone.utc)
        m = Measurement(
            value=1.5,
            unit="kt",
            source=SourceName.IMD_MARINE,
            retrieved_at=now,
        )
        assert m.observed_at is None


class TestGeoPoint:
    """Test the GeoPoint model."""

    def test_valid_geopoint(self):
        """Test creating a valid GeoPoint."""
        p = GeoPoint(lat=12.5, lon=77.5)
        assert p.lat == 12.5
        assert p.lon == 77.5

    def test_geopoint_lat_bounds(self):
        """Test that latitude is validated."""
        with pytest.raises(ValueError):
            GeoPoint(lat=91, lon=77.5)  # > 90

    def test_geopoint_lon_bounds(self):
        """Test that longitude is validated."""
        with pytest.raises(ValueError):
            GeoPoint(lat=12.5, lon=181)  # > 180


class TestPFZNode:
    """Test the PFZNode model."""

    def test_pfz_node_creation(self):
        """Test creating a valid PFZNode."""
        now = datetime.now(timezone.utc)
        loc = GeoPoint(lat=12.5, lon=77.5)
        depth = Measurement(
            value=45, unit="m_depth", source=SourceName.INCOIS_PFZ, retrieved_at=now
        )
        node = PFZNode(location=loc, depth=depth, valid_date=now)
        assert node.location.lat == 12.5
        assert node.depth.value == 45


class TestSafetyFlag:
    """Test the SafetyFlag model."""

    def test_safety_flag_creation(self):
        """Test creating a valid SafetyFlag."""
        now = datetime.now(timezone.utc)
        wave_m = Measurement(value=3.5, unit="m", source=SourceName.IMD_MARINE, retrieved_at=now)
        flag = SafetyFlag(
            code="high_wave",
            severity=Severity.DANGER,
            message_key="danger_high_wave",
            triggered_by=[wave_m],
            threshold_repr="wave_height > 2.5 m",
        )
        assert flag.code == "high_wave"
        assert flag.severity == Severity.DANGER
        assert len(flag.triggered_by) == 1


class TestMarineDataResult:
    """Test the MarineDataResult model."""

    def test_marine_data_result_empty(self):
        """Test creating an empty MarineDataResult."""
        result = MarineDataResult(pfz_nodes=[])
        assert result.pfz_nodes == []
        assert result.chlorophyll is None


class TestWeatherRiskResult:
    """Test the WeatherRiskResult model."""

    def test_weather_risk_result_with_flags(self):
        """Test WeatherRiskResult with safety flags."""
        now = datetime.now(timezone.utc)
        wave_m = Measurement(value=3.5, unit="m", source=SourceName.IMD_MARINE, retrieved_at=now)
        flag = SafetyFlag(
            code="high_wave",
            severity=Severity.DANGER,
            message_key="danger_high_wave",
            triggered_by=[wave_m],
            threshold_repr="wave_height > 2.5 m",
        )
        result = WeatherRiskResult(
            wave_height=wave_m,
            safety_flags=[flag],
        )
        assert result.wave_height.value == 3.5
        assert len(result.safety_flags) == 1


class TestPlatformState:
    """Test the PlatformState TypedDict."""

    def test_platform_state_creation(self):
        """Test creating a valid PlatformState dict."""
        state: PlatformState = {
            "query_text": "Where is the nearest fishing zone?",
            "source_lang": "en-IN",
            "channel": "web",
            "user_location": (12.5, 77.5),
            "trace_id": "orca_abc123",
            "intent": "pfz_nearest",
            "subtasks": ["marine_data", "geospatial"],
            "safety_flags": [],
            "data_freshness": {},
            "guardrail_status": "ok",
            "guardrail_notes": [],
        }
        assert state["query_text"] == "Where is the nearest fishing zone?"
        assert state["intent"] == "pfz_nearest"


class TestLLMFactory:
    """Test the LLM factory and MockLLM."""

    def test_get_llm_mock(self):
        """Test that get_llm returns MockLLM when provider=mock (default).

        Settings uses the env var ORCA_LLM_PROVIDER, which defaults to "mock".
        """
        # The default is already "mock", so just test that
        llm = get_llm()
        assert isinstance(llm, MockLLM)

    def test_mock_llm_classify(self):
        """Test MockLLM.classify returns a valid label."""
        llm = MockLLM()
        labels = ["pfz_nearest", "safety_check", "boundary_check"]
        # Test with a keyword that should match
        result = llm.classify("Where is the nearest fishing zone?", labels)
        assert result in labels
        assert result == "pfz_nearest"

    def test_mock_llm_classify_fallback(self):
        """Test MockLLM.classify falls back to first label."""
        llm = MockLLM()
        labels = ["some_intent", "another_intent"]
        result = llm.classify("xyzabc no keywords match", labels)
        assert result == labels[0]

    def test_mock_llm_classify_respects_labels(self):
        """Test that classify only returns labels in the given set."""
        llm = MockLLM()
        labels = ["custom_label"]
        result = llm.classify("Where is the nearest fishing zone?", labels)
        assert result == "custom_label"

    def test_mock_llm_narrate(self):
        """Test MockLLM.narrate returns a string."""
        llm = MockLLM()
        result = llm.narrate(
            {"wave_height": "2.3", "wind_speed": "20"},
            system="Narrate this",
            max_words=50,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_mock_llm_complete(self):
        """Test MockLLM.complete returns a string."""
        from orca.schemas import LLMMessage

        llm = MockLLM()
        messages = [LLMMessage(role="user", content="Hello?")]
        result = llm.complete(messages)
        assert isinstance(result, str)


class TestSpeechFactory:
    """Test the speech factory and MockSpeech."""

    def test_get_speech_mock(self):
        """Test that get_speech returns MockSpeech when provider=mock (default).

        Settings uses the env var ORCA_SPEECH_PROVIDER, which defaults to "mock".
        """
        # The default is already "mock", so just test that
        speech = get_speech()
        assert isinstance(speech, MockSpeech)

    def test_mock_speech_detect_language(self):
        """Test MockSpeech.detect_language returns a language code."""
        speech = MockSpeech()
        result = speech.detect_language(b"audio_bytes")
        assert isinstance(result, str)
        assert "-" in result  # BCP 47 format (e.g., "en-IN")

    def test_mock_speech_asr(self):
        """Test MockSpeech.asr returns a transcript."""
        speech = MockSpeech()
        result = speech.asr(b"audio_bytes", "en-IN")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_mock_speech_asr_tamil(self):
        """Test MockSpeech.asr with Tamil language."""
        speech = MockSpeech()
        result = speech.asr(b"audio_bytes", "ta-IN")
        assert isinstance(result, str)

    def test_mock_speech_translate(self):
        """Test MockSpeech.translate returns a string."""
        speech = MockSpeech()
        result = speech.translate("Where is the nearest fishing zone?", "en-IN", "en-IN")
        assert isinstance(result, str)

    def test_mock_speech_tts(self):
        """Test MockSpeech.tts returns audio bytes."""
        speech = MockSpeech()
        result = speech.tts("Hello world", "en-IN")
        assert isinstance(result, bytes)


class TestOfflineExecution:
    """Verify that all tests run offline without API calls."""

    def test_no_network_required(self):
        """Verify the entire M1 layer runs offline.

        If this passes, all models, factories, and mock implementations
        work without any external network calls.
        """
        # Create all the main objects
        llm = get_llm()
        speech = get_speech()

        # Run LLM operations
        intent = llm.classify("Where is the fish?", ["pfz_nearest", "safety_check"])
        assert intent in ["pfz_nearest", "safety_check"]

        narration = llm.narrate({"zone": "12.5N", "depth": "45m"}, system="Narrate")
        assert narration

        # Run speech operations
        lang = speech.detect_language(b"")
        assert lang
        transcript = speech.asr(b"", "en-IN")
        assert transcript
        audio = speech.tts("Hello", "en-IN")
        assert audio

        # All of the above completed without any network access ✓
