from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from backend.server import app
from backend.services.ai_provider import AiProviderError, CloudChatProvider, get_chat_provider


def test_chat_route_uses_provider_without_exposing_provider_details():
    provider = type("Provider", (), {"chat": AsyncMock(return_value="Pratham builds polished portfolio projects.")})()
    with patch("backend.routes.chat.get_chat_provider", return_value=provider):
        response = TestClient(app).post("/api/chat", json={"message": "What does Pratham build?"})

    assert response.status_code == 200
    assert response.json() == {"reply": "Pratham builds polished portfolio projects."}
    provider.chat.assert_awaited_once_with("What does Pratham build?")


def test_chat_route_returns_safe_unavailable_response():
    provider = type("Provider", (), {"chat": AsyncMock(side_effect=AiProviderError("The AI assistant is temporarily unavailable."))})()
    with patch("backend.routes.chat.get_chat_provider", return_value=provider):
        response = TestClient(app).post("/api/chat", json={"message": "Hello"})

    assert response.status_code == 503
    assert response.json()["detail"] == "The AI assistant is temporarily unavailable."


def test_cloud_provider_sends_api_key_only_in_server_side_authorization_header():
    provider = CloudChatProvider({
        "cloud_ai_base_url": "https://cloud.example/v1",
        "cloud_ai_api_key": "cloud-secret-key",
        "cloud_ai_model": "portfolio-model",
    })
    response = type("Response", (), {
        "raise_for_status": lambda self: None,
        "json": lambda self: {"choices": [{"message": {"content": "Hello from the hosted provider."}}]},
    })()

    import asyncio
    with patch("backend.services.ai_provider.httpx.AsyncClient.post", new_callable=AsyncMock, return_value=response) as post:
        result = asyncio.run(provider.chat("What is Pratham's name?"))

    assert result == "Hello from the hosted provider."
    assert post.call_args.args == ("https://cloud.example/v1/chat/completions",)
    assert post.call_args.kwargs["headers"] == {"Authorization": "Bearer cloud-secret-key"}
    assert "Visitor question: What is Pratham's name?" in post.call_args.kwargs["json"]["messages"][-1]["content"]


def test_provider_factory_selects_cloud_without_constructing_ollama():
    provider = get_chat_provider({"ai_provider": "cloud"})
    assert isinstance(provider, CloudChatProvider)
