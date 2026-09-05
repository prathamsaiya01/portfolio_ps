from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from backend.server import app
from backend.services.github_webhook_service import GitHubWebhookService

from tests.test_phase6_backend import FakeDb
from tests.test_phase7_backend import Db, project


REPO_ID = "1355830961"


def repository():
    return {
        "id": int(REPO_ID),
        "name": "igniteHackathon404Found",
        "full_name": "Heetshah21/igniteHackathon404Found",
        "owner": {"login": "Heetshah21"},
        "html_url": "https://github.com/Heetshah21/igniteHackathon404Found",
        "languages": ["TypeScript"],
        "topics": [],
        "contributors": ["prathamsaiya01"],
        "contribution_evidence": {"meaningful_contribution": True, "can_push": True, "authored_commit_count": 2},
    }


def test_admin_endpoint_requires_secret_and_email_suppression():
    with patch("backend.routes.admin_processing.get_settings", return_value={"admin_secret": "test-admin-secret"}):
        client = TestClient(app)
        missing = client.post(f"/api/admin/process-repository/{REPO_ID}")
        unsuppressed = client.post(
            f"/api/admin/process-repository/{REPO_ID}",
            headers={"X-Admin-Secret": "test-admin-secret"},
        )
    assert missing.status_code == 401
    assert unsuppressed.status_code == 400


def test_admin_endpoint_processes_only_one_repository_and_suppresses_side_effects():
    db = FakeDb()
    github = MagicMock()
    github.fetch_repository_by_id = AsyncMock(return_value={
        **repository(),
        "repository_name": "igniteHackathon404Found",
        "owner": "Heetshah21",
    })
    github.fetch_repository = AsyncMock(return_value={
        **repository(),
        "repository_name": "igniteHackathon404Found",
        "owner": "Heetshah21",
    })
    github.discover_repositories = AsyncMock(side_effect=AssertionError("discovery must not run"))
    analyzer = MagicMock()
    analyzer.analyze_project = AsyncMock(return_value={
        "summary": "AI unavailable",
        "scores": {},
        "evidence": ["GitHub facts"],
        "recommendation": "REVIEW",
        "overall_score": 0,
        "ai_analysis_status": "UNAVAILABLE",
    })
    email = MagicMock()
    email.send_candidate_email = AsyncMock(side_effect=AssertionError("email must not run"))
    processing_service = GitHubWebhookService(github_service=github, analyzer=analyzer, email_service=email)

    with patch("backend.routes.admin_processing.get_settings", return_value={"admin_secret": "test-admin-secret"}), \
         patch("backend.routes.admin_processing.get_database", return_value=db), \
         patch("backend.routes.admin_processing.GitHubService", return_value=github), \
         patch("backend.routes.admin_processing.GitHubWebhookService", return_value=processing_service):
        response = TestClient(app).post(
            f"/api/admin/process-repository/{REPO_ID}?email_suppressed=true",
            headers={"X-Admin-Secret": "test-admin-secret"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["github_repo_id"] == REPO_ID
    assert body["full_name"] == "Heetshah21/igniteHackathon404Found"
    assert body["email_sent"] is False
    assert body["published"] is False
    assert len(db.projects.documents) == 1
    assert len(db.candidates.documents) == 1
    assert db.candidates.documents[0]["recommendation"] == "REVIEW"
    github.fetch_repository_by_id.assert_awaited_once_with(REPO_ID)
    github.discover_repositories.assert_not_awaited()
    email.send_candidate_email.assert_not_awaited()


def test_admin_endpoint_rejects_non_numeric_repository_id():
    with patch("backend.routes.admin_processing.get_settings", return_value={"admin_secret": "test-admin-secret"}):
        response = TestClient(app).post(
            "/api/admin/process-repository/not-numeric?email_suppressed=true",
            headers={"X-Admin-Secret": "test-admin-secret"},
        )
    assert response.status_code == 400


def test_webhook_processor_flags_skip_publishing_and_email():
    db = FakeDb()
    github = MagicMock()
    github.get_user_contribution_evidence = AsyncMock(return_value={"meaningful_contribution": True, "can_push": True})
    github.fetch_repository = AsyncMock(return_value=repository())
    github.discover_repositories = AsyncMock(side_effect=AssertionError("discovery must not run"))
    analyzer = MagicMock()
    analyzer.analyze_project = AsyncMock(return_value={"scores": {}, "evidence": ["facts"], "overall_score": 0, "recommendation": "REVIEW", "ai_analysis_status": "UNAVAILABLE"})
    email = MagicMock()
    email.send_candidate_email = AsyncMock()
    publishing = MagicMock()
    publishing.sync_project_metadata = AsyncMock(side_effect=AssertionError("publishing must not run"))
    service = GitHubWebhookService(github_service=github, analyzer=analyzer, email_service=email)

    import asyncio
    with patch("backend.services.github_webhook_service.PortfolioPublishingService", return_value=publishing):
        result = asyncio.run(service.process(
            "push",
            {"repository": {"id": int(REPO_ID), "name": "igniteHackathon404Found", "owner": {"login": "Heetshah21"}}},
            db,
            email_suppressed=True,
            sync_published_metadata=False,
        ))

    assert result["candidate_decision"] == "REVIEW"
    assert result["email_status"] == "SUPPRESSED"
    github.discover_repositories.assert_not_awaited()
    email.send_candidate_email.assert_not_awaited()
    publishing.sync_project_metadata.assert_not_awaited()


def test_republish_approved_candidate_is_idempotent_and_does_not_email_or_token():
    candidate = {
        "candidate_id": "candidate-repair",
        "github_repo_id": REPO_ID,
        "candidate_status": "APPROVED",
        "repository_name": "igniteHackathon404Found",
        "full_name": "Heetshah21/igniteHackathon404Found",
        "suggested_title": "Ignite Hackathon",
        "suggested_description": "A verified project.",
        "github_url": "https://github.com/Heetshah21/igniteHackathon404Found",
        "languages": ["TypeScript"],
        "technologies": ["React"],
        "topics": [],
    }
    db = Db(projects=[project()])
    db.candidates.records.append(candidate)

    with patch("backend.routes.admin_processing.get_database", return_value=db), \
         patch("backend.routes.admin_processing.get_settings", return_value={"admin_secret": "test-admin-secret"}), \
         patch("backend.services.email_service.EmailService") as email_service, \
         patch("backend.services.approval_token_service.ApprovalTokenService") as token_service:
        client = TestClient(app)
        first = client.post("/api/admin/republish-candidate/candidate-repair", headers={"X-Admin-Secret": "test-admin-secret"})
        second = client.post("/api/admin/republish-candidate/candidate-repair", headers={"X-Admin-Secret": "test-admin-secret"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["candidate_status"] == "APPROVED"
    assert first.json()["published"] is True
    assert first.json()["publishing_status"] == "PUBLISHED"
    assert first.json()["published_project_id"] == second.json()["published_project_id"]
    assert len(db.published_projects.records) == 1
    email_service.assert_not_called()
    token_service.assert_not_called()


def test_republish_requires_approved_candidate():
    db = Db(projects=[project()])
    db.candidates.records.append({"candidate_id": "candidate-review", "github_repo_id": REPO_ID, "candidate_status": "REVIEW"})
    with patch("backend.routes.admin_processing.get_database", return_value=db), patch("backend.routes.admin_processing.get_settings", return_value={"admin_secret": "test-admin-secret"}):
        response = TestClient(app).post("/api/admin/republish-candidate/candidate-review", headers={"X-Admin-Secret": "test-admin-secret"})
    assert response.status_code == 409
    assert db.published_projects.records == []
