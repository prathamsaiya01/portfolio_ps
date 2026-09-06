"""Local Chatterbox Nano text-to-speech provider.

The model is intentionally imported and initialized only when it is first used.
"""

from __future__ import annotations

import asyncio
import io
import logging
import threading
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict

from backend.config import get_settings
from backend.services.elevenlabs_service import TextToSpeechError

logger = logging.getLogger(__name__)


class ChatterboxService:
    _model: Any = None
    _model_lock = threading.Lock()
    _audio_cache: OrderedDict[str, bytes] = OrderedDict()
    _cache_lock = threading.Lock()
    _cache_size = 32

    def __init__(self, settings: Dict[str, Any] | None = None):
        self.settings = settings or get_settings()

    def _voice_path(self) -> Path:
        value = self.settings.get("chatterbox_voice_path")
        if not value:
            raise TextToSpeechError("Chatterbox voice reference is not configured.")
        path = Path(str(value)).expanduser()
        if not path.is_file():
            logger.error("Chatterbox voice reference is unavailable: path=%s", path)
            raise TextToSpeechError("Chatterbox voice reference is unavailable.")
        return path

    def _get_model(self) -> Any:
        if type(self)._model is None:
            with type(self)._model_lock:
                if type(self)._model is None:
                    device = str(self.settings.get("chatterbox_device") or "cpu")
                    try:
                        # Keep optional dependencies out of normal backend startup.
                        from chatterbox.tts_turbo import ChatterboxTurboTTS

                        type(self)._model = ChatterboxTurboTTS.from_pretrained(device=device, nano=True)
                        logger.info("Chatterbox Nano model initialized: device=%s", device)
                    except Exception as exc:
                        logger.exception("Chatterbox Nano initialization failed: exception_type=%s", type(exc).__name__)
                        raise TextToSpeechError("Voice is temporarily unavailable.") from exc
        return type(self)._model

    def _synthesize_sync(self, text: str) -> bytes:
        clean_text = text.strip()
        if not clean_text:
            raise TextToSpeechError("Voice cannot be generated for empty text.")
        with type(self)._cache_lock:
            cached = type(self)._audio_cache.get(clean_text)
            if cached is not None:
                type(self)._audio_cache.move_to_end(clean_text)
                return cached

        voice_path = self._voice_path()
        model = self._get_model()
        try:
            waveform = model.generate(clean_text, audio_prompt_path=str(voice_path))
            # Chatterbox returns a torch waveform. torchaudio writes directly to memory.
            import torchaudio

            output = io.BytesIO()
            sample_rate = int(getattr(model, "sr", getattr(model, "sample_rate", 24000)))
            torchaudio.save(output, waveform.detach().cpu(), sample_rate, format="wav")
            audio = output.getvalue()
        except TextToSpeechError:
            raise
        except Exception as exc:
            logger.exception("Chatterbox speech synthesis failed: exception_type=%s", type(exc).__name__)
            raise TextToSpeechError("Voice is temporarily unavailable.") from exc
        if not audio:
            logger.error("Chatterbox speech synthesis failed: exception_type=EmptyAudioResponse")
            raise TextToSpeechError("Voice is temporarily unavailable.")
        with type(self)._cache_lock:
            type(self)._audio_cache[clean_text] = audio
            type(self)._audio_cache.move_to_end(clean_text)
            while len(type(self)._audio_cache) > type(self)._cache_size:
                type(self)._audio_cache.popitem(last=False)
        return audio

    async def synthesize(self, text: str) -> bytes:
        return await asyncio.to_thread(self._synthesize_sync, text)
