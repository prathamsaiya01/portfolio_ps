from __future__ import annotations

import logging
from typing import Any, Dict

import httpx

from backend.config import get_settings

logger = logging.getLogger(__name__)


class TextToSpeechError(RuntimeError):
    """Raised when configured text-to-speech cannot generate playable audio."""


class ElevenLabsService:
    def __init__(self, settings: Dict[str, Any] | None = None):
        self.settings = settings or get_settings()

    async def synthesize(self, text: str) -> bytes:
        api_key = self.settings.get("elevenlabs_api_key")
        voice_id = self.settings.get("elevenlabs_voice_id")
        model_id = self.settings.get("elevenlabs_model_id") or "eleven_multilingual_v2"
        output_format = self.settings.get("elevenlabs_output_format") or "mp3_44100_128"
        if not api_key or not voice_id:
            raise TextToSpeechError("Voice is not configured.")
        if not text or not text.strip():
            raise TextToSpeechError("Voice cannot be generated for empty text.")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                    params={"output_format": output_format},
                    headers={"xi-api-key": str(api_key), "Accept": "audio/mpeg"},
                    json={"text": text.strip(), "model_id": model_id},
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("ElevenLabs speech synthesis failed: exception_type=%s", type(exc).__name__)
            raise TextToSpeechError("Voice is temporarily unavailable.") from exc

        audio = response.content
        if not audio:
            logger.error("ElevenLabs speech synthesis failed: exception_type=EmptyAudioResponse")
            raise TextToSpeechError("Voice is temporarily unavailable.")
        return audio
