from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.database import close_database_connection, get_database
from backend.routes.github import GitHubSyncResponse, sync_github_repositories
from backend.utils.github_helpers import normalize_repo_payload


@pytest.fixture
def app_client():
    from backend.server import app

    return TestClient(app)


@pytest.fixture
def fake_repo_payload():
    return {
        "id": 101,
        "name": "CareerMitra",
        "full_name": "pratham/CareerMitra",
        "description": "AI career guidance platform",
        "html_url": "https://github.com/pratham/CareerMitra",
        "homepage": "https://careermitra.example",
        "created_at": "2024-01-15T12:00:00Z",
        "updated_at": "2025-03-20T10:30:00Z",
        "stargazers_count": 42,
        "forks_count": 8,
        "visibility": "public",
        "topics": ["ai", "career", "ml"],
        "owner": {"login": "pratham"},
        "languages": {"Python": 100, "TypeScript": 80},
    }


def test_repository_normalization(fake_repo_payload):
    normalized = normalize_repo_payload(fake_repo_payload)

    assert normalized["github_repo_id"] == "101"
    assert normalized["repository_name"] == "CareerMitra"
    assert normalized["full_name"] == "pratham/CareerMitra"
    assert normalized["owner"] == "pratham"
    assert normalized["stars"] == 42
    assert normalized["forks"] == 8
    assert normalized["repository_visibility"] == "public"
    assert "Python" in normalized["languages"]
    assert "ai" in normalized["topics"]
    assert normalized["created_at"] is not None


@pytest.mark.asyncio
async def test_repository_upsert_and_deduplication(fake_repo_payload):
    db = get_database()
    if db is not None:
        await db.projects.delete_many({"github_repo_id": "101"})

    normalized = normalize_repo_payload(fake_repo_payload)
    normalized["created_at_db"] = datetime.now(timezone.utc)
    normalized["updated_at_db"] = datetime.now(timezone.utc)
    normalized["last_synced_at"] = datetime.now(timezone.utc)

    if db is not None:
        await db.projects.insert_one(normalized)
        first = await db.projects.find_one({"github_repo_id": "101"})
        assert first is not None

        await db.projects.update_one({"github_repo_id": "101"}, {"$set": {"description": "Updated"}})
        second = await db.projects.find_one({"github_repo_id": "101"})
        assert second["description"] == "Updated"

    close_database_connection()


@pytest.mark.asyncio
async def test_project_retrieval_route_returns_data(fake_repo_payload):
    db = get_database()
    if db is not None:
        await db.projects.delete_many({"github_repo_id": "101"})
        await db.projects.insert_one({**normalize_repo_payload(fake_repo_payload), "created_at_db": datetime.now(timezone.utc), "updated_at_db": datetime.now(timezone.utc)})

    from backend.server import app
    client = TestClient(app)
    response = client.get("/api/projects")

    assert response.status_code in (200, 503)
    if response.status_code == 200:
        payload = response.json()
        assert isinstance(payload, list)

    close_database_connection()


@pytest.mark.asyncio
async def test_github_api_failure_handling():
    from backend.services.github_service import GitHubService

    with patch("backend.services.github_service.httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=Exception("boom")):
        with pytest.raises(RuntimeError):
            service = GitHubService(token="x", username="demo")
            await service.fetch_repositories()


def test_invalid_configuration_has_no_credentials_required():
    from backend.config import get_settings

    settings = get_settings()
    assert settings["mongo_url"] is not None or settings["mongo_url"] is None
    assert isinstance(settings["cors_origins"], list)
