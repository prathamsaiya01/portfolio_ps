import asyncio
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.server import app
from backend.services.chatterbox_service import ChatterboxService
from backend.services.elevenlabs_service import TextToSpeechError
from backend.services.tts_provider import ChatterboxTtsProvider, ElevenLabsTtsProvider, get_tts_provider


@pytest.fixture(autouse=True)
def reset_chatterbox_state():
    ChatterboxService._model = None
    ChatterboxService._audio_cache.clear()
    yield
    ChatterboxService._model = None
    ChatterboxService._audio_cache.clear()


def test_tts_provider_selection_preserves_elevenlabs_and_selects_chatterbox():
    assert isinstance(get_tts_provider({"tts_provider": "elevenlabs"}), ElevenLabsTtsProvider)
    assert isinstance(get_tts_provider({"tts_provider": "chatterbox"}), ChatterboxTtsProvider)
    with pytest.raises(TextToSpeechError, match="not supported"):
        get_tts_provider({"tts_provider": "unknown"})


def test_chatterbox_requires_an_existing_voice_reference():
    service = ChatterboxService({"chatterbox_voice_path": "not-a-real-reference.wav"})
    with pytest.raises(TextToSpeechError, match="reference is unavailable"):
        asyncio.run(service.synthesize("Hello"))


def test_chatterbox_model_is_lazy_and_cached(tmp_path):
    reference = tmp_path / "voice.wav"
    reference.write_bytes(b"not inspected by mocked model")
    fake_model = MagicMock(sr=24000)
    fake_model.generate.return_value = MagicMock()
    fake_model.generate.return_value.detach.return_value.cpu.return_value = "waveform"

    def write_wav(destination, waveform, sample_rate, format):
        assert waveform == "waveform"
        assert sample_rate == 24000
        assert format == "wav"
        destination.write(b"RIFFfake-wav")

    service = ChatterboxService({"chatterbox_device": "cpu", "chatterbox_voice_path": str(reference)})
    with patch("backend.services.chatterbox_service.ChatterboxService._get_model", return_value=fake_model) as get_model, \
         patch("torchaudio.save", side_effect=write_wav):
        assert asyncio.run(service.synthesize("Same response")) == b"RIFFfake-wav"
        assert asyncio.run(service.synthesize("Same response")) == b"RIFFfake-wav"

    assert get_model.call_count == 1
    assert fake_model.generate.call_count == 1


def test_chatterbox_route_returns_wav_and_safe_failure():
    provider = MagicMock(media_type="audio/wav")
    provider.synthesize = __import__("unittest.mock", fromlist=["AsyncMock"]).AsyncMock(return_value=b"RIFFfake-wav")
    with patch("backend.routes.chat.get_tts_provider", return_value=provider):
        response = TestClient(app).post("/api/chat/tts", json={"text": "A portfolio answer."})
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.content == b"RIFFfake-wav"

    provider.synthesize.side_effect = TextToSpeechError("offline")
    with patch("backend.routes.chat.get_tts_provider", return_value=provider):
        failed = TestClient(app).post("/api/chat/tts", json={"text": "A portfolio answer."})
    assert failed.status_code == 503
    assert failed.json()["detail"] == "Voice unavailable right now."
