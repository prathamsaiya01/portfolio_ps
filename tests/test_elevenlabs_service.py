import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.server import app
from backend.services.elevenlabs_service import ElevenLabsService, TextToSpeechError
from backend.services.tts_provider import ElevenLabsTtsProvider


def test_elevenlabs_service_uses_configured_server_side_voice_and_returns_mp3():
    service = ElevenLabsService({
        "elevenlabs_api_key": "eleven-secret-key",
        "elevenlabs_voice_id": "cloned-voice-id",
        "elevenlabs_model_id": "eleven_multilingual_v2",
        "elevenlabs_output_format": "mp3_44100_128",
    })
    response = MagicMock(content=b"fake-mp3")
    response.raise_for_status.return_value = None

    with patch("backend.services.elevenlabs_service.httpx.AsyncClient.post", new_callable=AsyncMock, return_value=response) as post:
        audio = asyncio.run(service.synthesize("Hello from Pratham AI."))

    assert audio == b"fake-mp3"
    assert post.call_args.args == ("https://api.elevenlabs.io/v1/text-to-speech/cloned-voice-id",)
    assert post.call_args.kwargs["params"] == {"output_format": "mp3_44100_128"}
    assert post.call_args.kwargs["headers"]["xi-api-key"] == "eleven-secret-key"
    assert post.call_args.kwargs["json"] == {"text": "Hello from Pratham AI.", "model_id": "eleven_multilingual_v2"}


def test_elevenlabs_service_validates_configuration():
    with pytest.raises(TextToSpeechError, match="not configured"):
        asyncio.run(ElevenLabsService({}).synthesize("Hello"))


def test_elevenlabs_failure_is_safe_and_does_not_log_api_key(caplog):
    service = ElevenLabsService({"elevenlabs_api_key": "eleven-secret-key", "elevenlabs_voice_id": "cloned-voice-id"})
    request = httpx.Request("POST", "https://api.elevenlabs.io/v1/text-to-speech/cloned-voice-id")
    provider_error = httpx.HTTPStatusError("Bad request", request=request, response=httpx.Response(400, request=request))

    with patch("backend.services.elevenlabs_service.httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=provider_error):
        with caplog.at_level(logging.ERROR):
            with pytest.raises(TextToSpeechError, match="temporarily unavailable"):
                asyncio.run(service.synthesize("Hello"))

    assert "eleven-secret-key" not in caplog.text
    assert "exception_type=HTTPStatusError" in caplog.text


def test_tts_route_returns_audio_and_voice_failures_do_not_affect_text_chat():
    tts_service = MagicMock()
    tts_service.media_type = "audio/mpeg"
    tts_service.synthesize = AsyncMock(return_value=b"fake-mp3")
    with patch("backend.routes.chat.get_tts_provider", return_value=tts_service):
        response = TestClient(app).post("/api/chat/tts", json={"text": "A portfolio answer."})

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert response.content == b"fake-mp3"

    tts_service.synthesize = AsyncMock(side_effect=TextToSpeechError("offline"))
    with patch("backend.routes.chat.get_tts_provider", return_value=tts_service):
        failed = TestClient(app).post("/api/chat/tts", json={"text": "A portfolio answer."})

    assert failed.status_code == 503
    assert failed.json()["detail"] == "Voice unavailable right now."
