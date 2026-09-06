from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from backend.services.ai_provider import AiProviderError, get_chat_provider
from backend.services.elevenlabs_service import TextToSpeechError
from backend.services.tts_provider import get_tts_provider

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class ChatResponse(BaseModel):
    reply: str


class TextToSpeechRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        reply = await get_chat_provider().chat(request.message.strip())
    except AiProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None
    return ChatResponse(reply=reply)


@router.post("/tts", response_class=Response)
async def text_to_speech(request: TextToSpeechRequest):
    try:
        provider = get_tts_provider()
        audio = await provider.synthesize(request.text)
    except TextToSpeechError:
        raise HTTPException(status_code=503, detail="Voice unavailable right now.") from None
    return Response(content=audio, media_type=provider.media_type)
