from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from backend.server import app


class FakeDatabase:
    def __init__(self, count=0, ping_error=None, count_error=None):
        self.client = MagicMock()
        self.client.admin.command = AsyncMock(side_effect=ping_error)
        self.published_projects = MagicMock()
        self.published_projects.count_documents = AsyncMock(return_value=count, side_effect=count_error)


def test_mongodb_diagnostic_success():
    database = FakeDatabase(count=3)
    with patch("backend.routes.diagnostics.get_database", return_value=database), patch(
        "backend.routes.diagnostics.get_settings",
        return_value={"mongo_url": "configured", "db_name": "configured"},
    ):
        response = TestClient(app).get("/api/diagnostics/mongodb")

    assert response.status_code == 200
    assert response.json() == {
        "mongo_url_configured": True,
        "db_name_configured": True,
        "connection_created": True,
        "ping": "ok",
        "published_projects_access": "ok",
        "published_projects_count": 3,
        "error_type": "",
        "error_message": "",
    }


def test_mongodb_diagnostic_ping_failure_is_safe():
    database = FakeDatabase(ping_error=RuntimeError("mongodb://user:password@example.invalid connection failed"))
    with patch("backend.routes.diagnostics.get_database", return_value=database), patch(
        "backend.routes.diagnostics.get_settings",
        return_value={"mongo_url": "configured", "db_name": "configured"},
    ):
        response = TestClient(app).get("/api/diagnostics/mongodb")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ping"] == "failed"
    assert payload["published_projects_access"] == "failed"
    assert payload["error_type"] == "RuntimeError"
    assert "password" not in payload["error_message"]
    assert "mongodb://[redacted]@" in payload["error_message"]


def test_mongodb_diagnostic_returns_503_when_database_unavailable():
    with patch("backend.routes.diagnostics.get_database", return_value=None), patch(
        "backend.routes.diagnostics.get_settings",
        return_value={"mongo_url": "", "db_name": ""},
    ):
        response = TestClient(app).get("/api/diagnostics/mongodb")

    assert response.status_code == 503
    payload = response.json()["detail"]
    assert payload["connection_created"] is False
    assert payload["error_type"] == "DatabaseNotConfigured"
    assert payload["mongo_url_configured"] is False
    assert payload["db_name_configured"] is False
    assert "mongodb://" not in str(payload)
