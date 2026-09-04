from __future__ import annotations

import hashlib
import hmac
import json
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from backend.server import app
from backend.services.github_webhook_service import GitHubWebhookService


class FakeCursor:
    def __init__(self, records):
        self.records = records

    async def to_list(self, length=100):
        return list(self.records)[:length]


class FakeCollection:
    def __init__(self):
        self.documents = []

    async def find_one(self, query):
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items() if not isinstance(value, dict)):
                return dict(document)
        return None

    def find(self, query):
        records = []
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items() if not isinstance(value, dict)):
                records.append(dict(document))
        return FakeCursor(records)

    async def insert_one(self, document):
        self.documents.append(dict(document))

    async def update_one(self, query, update):
        document = await self.find_one(query)
        if document is None:
            return
        for stored in self.documents:
            if stored.get("candidate_id") == document.get("candidate_id") or stored.get("github_repo_id") == document.get("github_repo_id"):
                stored.update(update.get("$set", {}))
                for key, value in update.get("$inc", {}).items():
                    stored[key] = stored.get(key, 0) + value
                return


class FakeDb:
    def __init__(self):
        self.projects = FakeCollection()
        self.candidates = FakeCollection()


def signed(body: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def payload():
    return {
        "ref": "refs/heads/main",
        "repository": {
            "id": 501,
            "name": "CareerMitra",
            "full_name": "pratham/CareerMitra",
            "html_url": "https://github.com/pratham/CareerMitra",
            "owner": {"login": "pratham"},
        },
    }


def test_signature_verification_and_event_filtering():
    body = json.dumps(payload()).encode()
    signature = signed(body, "webhook-secret")
    GitHubWebhookService.verify_signature(body, signature, "webhook-secret")
    assert GitHubWebhookService.is_relevant_event("push", payload())
    assert GitHubWebhookService.is_relevant_event("pull_request", {**payload(), "action": "synchronize"})
    assert not GitHubWebhookService.is_relevant_event("issues", payload())
    assert not GitHubWebhookService.is_relevant_event("pull_request", {**payload(), "action": "labeled"})


def test_webhook_pipeline_syncs_analyzes_promotes_and_emails():
    db = FakeDb()
    github = MagicMock()
    github.fetch_repository = AsyncMock(return_value={
        "id": 501,
        "name": "CareerMitra",
        "full_name": "pratham/CareerMitra",
        "html_url": "https://github.com/pratham/CareerMitra",
        "owner": {"login": "pratham"},
        "description": "Career planning tool",
        "languages": ["Python"],
        "topics": ["career", "automation"],
        "stargazers_count": 32,
    })
    analyzer = MagicMock()
    analyzer.analyze_project = AsyncMock(return_value={
        "summary": "Evidence-backed analysis",
        "scores": {
            "technical_depth": 92,
            "complexity": 88,
            "originality": 90,
            "impact": 87,
            "engineering_quality": 91,
            "maturity": 84,
            "collaboration": 80,
            "portfolio_fit": 91,
        },
        "evidence": ["Repository contains a documented automation workflow"],
        "recommendation": "CANDIDATE",
        "overall_score": 89,
    })
    email = MagicMock()
    email.send_candidate_email = AsyncMock(return_value={"tokens": {}})
    service = GitHubWebhookService(github_service=github, analyzer=analyzer, email_service=email)

    import asyncio
    result = asyncio.run(service.process("push", payload(), db, delivery_id="delivery-1"))

    assert result["status"] == "processed"
    assert result["candidate_decision"] == "CANDIDATE"
    assert result["email_status"] == "SENT"
    assert len(db.projects.documents) == 1
    assert len(db.candidates.documents) == 1
    assert db.candidates.documents[0]["candidate_status"] == "CANDIDATE"
    email.send_candidate_email.assert_awaited_once()

    duplicate = asyncio.run(service.process("push", payload(), db, delivery_id="delivery-1"))
    assert duplicate["status"] == "duplicate"
    assert email.send_candidate_email.await_count == 1


def test_terminal_candidate_decision_is_preserved():
    db = FakeDb()
    db.projects.documents.append({"github_repo_id": "501", "repository_name": "CareerMitra"})
    db.candidates.documents.append({
        "candidate_id": "candidate-1",
        "github_repo_id": "501",
        "candidate_status": "APPROVED",
        "recommendation": "APPROVED",
        "decision": "APPROVED",
        "email_status": "SENT",
    })
    github = MagicMock()
    github.fetch_repository = AsyncMock(return_value={"id": 501, "name": "CareerMitra", "owner": {"login": "pratham"}, "topics": [], "languages": []})
    analyzer = MagicMock()
    analyzer.analyze_project = AsyncMock(return_value={"scores": {"technical_depth": 90, "portfolio_fit": 90}, "evidence": ["repo"], "overall_score": 90, "recommendation": "CANDIDATE"})
    email = MagicMock()
    email.send_candidate_email = AsyncMock()
    service = GitHubWebhookService(github_service=github, analyzer=analyzer, email_service=email)

    import asyncio
    asyncio.run(service.process("push", payload(), db, delivery_id="delivery-2"))

    assert db.candidates.documents[0]["candidate_status"] == "APPROVED"
    assert db.candidates.documents[0]["decision"] == "APPROVED"
    email.send_candidate_email.assert_not_awaited()


def test_webhook_endpoint_rejects_invalid_signature(monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "webhook-secret")
    body = json.dumps(payload()).encode()
    with patch("backend.routes.github_webhook.get_database", return_value=MagicMock()):
        response = TestClient(app).post(
            "/api/github/webhook",
            content=body,
            headers={"X-GitHub-Event": "push", "X-Hub-Signature-256": "sha256=invalid"},
        )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid webhook signature"


def test_webhook_endpoint_accepts_valid_signature(monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "webhook-secret")
    body = json.dumps(payload()).encode()
    with patch("backend.routes.github_webhook.get_database", return_value=MagicMock()), patch("backend.routes.github_webhook.GitHubWebhookService") as service_class:
        service_class.verify_signature.return_value = None
        service_class.return_value.process = AsyncMock(return_value={"status": "ignored", "event": "ping"})
        response = TestClient(app).post(
            "/api/github/webhook",
            content=body,
            headers={"X-GitHub-Event": "ping", "X-Hub-Signature-256": signed(body, "webhook-secret")},
        )
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
