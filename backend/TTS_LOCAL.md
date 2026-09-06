# Local Chatterbox TTS

Chatterbox is supported for local integration only. Configure the backend environment with:

```env
TTS_PROVIDER=chatterbox
CHATTERBOX_DEVICE=cpu
CHATTERBOX_VOICE_PATH=D:\path\to\private-voice-reference.wav
```

Run the backend with the Python interpreter from the environment where Chatterbox Nano is installed, for example:

```powershell
& D:\portfolio\voice-nano-env\Scripts\python.exe -m uvicorn backend.server:app --host 127.0.0.1 --port 8002
```

Keep the voice-reference WAV private and local; it is not served or stored by the application. The model loads on the first TTS request and generated audio stays only in a small in-memory cache. Set `TTS_PROVIDER=elevenlabs` to retain the existing ElevenLabs provider and its `ELEVENLABS_*` settings.
