from __future__ import annotations

from typing import Any, Dict, Protocol

import httpx

from backend.config import get_settings
from backend.services.ollama_service import OllamaService, OllamaServiceError


class AiProviderError(RuntimeError):
    """Raised when the configured chat provider cannot return a response."""


class ChatProvider(Protocol):
    async def chat(self, message: str) -> str:
        """Return a portfolio-assistant response for a visitor message."""


class OllamaChatProvider:
    def __init__(self, service: OllamaService | None = None):
        self.service = service or OllamaService()

    async def chat(self, message: str) -> str:
        prompt = (
            "You are Pratham AI, a concise assistant for Pratham's portfolio website. "
            "Answer only about Pratham's projects, skills, and contact information. "
            "Do not invent facts. If the portfolio does not establish an answer, say so.\n\n"
            f"Visitor: {message}\nPratham AI:"
        )
        try:
            return await self.service.generate_chat_response(prompt)
        except OllamaServiceError as exc:
            raise AiProviderError("The AI assistant is temporarily unavailable.") from exc


class CloudChatProvider:
    """OpenAI-compatible hosted chat transport configured entirely on the server."""

    def __init__(self, settings: Dict[str, Any] | None = None):
        self.settings = settings or get_settings()

    async def chat(self, message: str) -> str:
        base_url = self.settings.get("cloud_ai_base_url")
        api_key = self.settings.get("cloud_ai_api_key")
        model = self.settings.get("cloud_ai_model")
        if not base_url or not api_key or not model:
            raise AiProviderError("The cloud AI provider is not configured.")

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are Pratham AI, a concise assistant for Pratham's portfolio. Do not invent facts.",
                },
                {"role": "user", "content": message},
            ],
            "temperature": 0.4,
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{str(base_url).rstrip('/')}/chat/completions",
                    json=payload,
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                response.raise_for_status()
                body = response.json()
            content = body["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            raise AiProviderError("The AI assistant is temporarily unavailable.") from exc

        if not isinstance(content, str) or not content.strip():
            raise AiProviderError("The AI assistant returned an empty response.")
        return content.strip()


def get_chat_provider(settings: Dict[str, Any] | None = None) -> ChatProvider:
    configured_settings = settings or get_settings()
    provider = str(configured_settings.get("ai_provider") or "ollama").lower()
    if provider == "ollama":
        return OllamaChatProvider()
    if provider == "cloud":
        return CloudChatProvider(configured_settings)
    raise AiProviderError("The configured AI provider is not supported.")
