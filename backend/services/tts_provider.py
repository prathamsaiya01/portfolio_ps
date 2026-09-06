"""Server-side text-to-speech provider selection."""

from __future__ import annotations

from typing import Any, Dict, Protocol

from backend.config import get_settings
from backend.services.chatterbox_service import ChatterboxService
from backend.services.elevenlabs_service import ElevenLabsService, TextToSpeechError


class TextToSpeechProvider(Protocol):
    media_type: str

    async def synthesize(self, text: str) -> bytes: ...


class ElevenLabsTtsProvider(ElevenLabsService):
    media_type = "audio/mpeg"


class ChatterboxTtsProvider(ChatterboxService):
    media_type = "audio/wav"


def get_tts_provider(settings: Dict[str, Any] | None = None) -> TextToSpeechProvider:
    configured_settings = settings or get_settings()
    provider = str(configured_settings.get("tts_provider") or "elevenlabs").lower()
    if provider == "elevenlabs":
        return ElevenLabsTtsProvider(configured_settings)
    if provider == "chatterbox":
        return ChatterboxTtsProvider(configured_settings)
    raise TextToSpeechError("The configured TTS provider is not supported.")
