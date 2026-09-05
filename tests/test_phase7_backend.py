from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.models.published_project import PublishedProject
from backend.routes.portfolio import get_published_projects
from backend.server import app
from backend.services.approval_service import ApprovalService
from backend.services.approval_token_service import ApprovalTokenService
from backend.services.portfolio_publishing import PortfolioPublishingError, PortfolioPublishingService


class Cursor:
    def __init__(self, records):
        self.records = list(records)

    def sort(self, *args):
        if len(args) == 2:
            field, direction = args
        elif args:
            field, direction = args[0]
        else:
            field, direction = "display_order", 1
        if field:
            self.records.sort(key=lambda item: item.get(field, 0) or 0, reverse=direction < 0)
        return self

    async def to_list(self, length=500):
        return self.records[:length]


class Collection:
    def __init__(self, records=None):
        self.records = list(records or [])

    async def find_one(self, query):
        for item in self.records:
            if all(item.get(key) == value for key, value in query.items()):
                return dict(item)
        return None

    def find(self, query):
        return Cursor([item for item in self.records if all(item.get(key) == value for key, value in query.items())])

    async def insert_one(self, document):
        self.records.append(dict(document))

    async def update_one(self, query, update):
        for item in self.records:
            if all(item.get(key) == value for key, value in query.items()):
                item.update(update.get("$set", {}))
                return


class Db:
    def __init__(self, published=None, projects=None):
        self.published_projects = Collection(published)
        self.projects = Collection(projects)
        self.candidates = Collection()


def candidate(status="APPROVED", **extra):
    return {
        "candidate_id": "candidate-7",
        "github_repo_id": "7001",
        "candidate_status": status,
        "suggested_title": "CareerMitra",
        "suggested_description": "A career planning tool.",
        "repository_name": "CareerMitra",
        "github_url": "https://github.com/pratham/CareerMitra",
        "languages": ["Python"],
        "technologies": ["FastAPI"],
        "topics": ["career"],
        "featured": False,
        **extra,
    }


def project():
    return {
        "github_repo_id": "7001",
        "repository_name": "CareerMitra",
        "description": "A career planning tool.",
        "github_url": "https://github.com/pratham/CareerMitra",
        "homepage_url": "https://careermitra.example.com",
        "languages": ["Python"],
        "detected_technologies": ["FastAPI"],
        "topics": ["career"],
    }


@pytest.mark.asyncio
async def test_approved_candidate_publishes_and_republishing_is_idempotent():
    db = Db(projects=[project()])
    service = PortfolioPublishingService()
    first = await service.publish_approved_candidate(db, candidate(), project())
    second = await service.publish_approved_candidate(db, candidate(), project())

    assert first["status"] == "PUBLISHED"
    assert first["source"] == "GITHUB_APPROVAL"
    assert first["display_order"] == 1
    assert second["id"] == first["id"]
    assert len(db.published_projects.records) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["REJECTED", "REVIEW", "IGNORE"])
async def test_non_approved_candidate_does_not_publish(status):
    db = Db(projects=[project()])
    with pytest.raises(PortfolioPublishingError):
        await PortfolioPublishingService().publish_approved_candidate(db, candidate(status), project())
    assert db.published_projects.records == []


@pytest.mark.asyncio
async def test_display_order_and_manual_fields_are_preserved():
    existing = {
        **PortfolioPublishingService._new_record(candidate(), project(), datetime.now(timezone.utc), 3),
        "title": "Curated CareerMitra",
        "description": "Curated copy",
        "featured": True,
        "display_order": 7,
        "title_manual": True,
        "description_manual": True,
    }
    db = Db(published=[existing], projects=[project()])
    updated = await PortfolioPublishingService().publish_approved_candidate(
        db,
        candidate(suggested_title="AI CareerMitra", suggested_description="Generated copy"),
        {**project(), "description": "New repository description", "languages": ["Python", "TypeScript"]},
    )
    assert updated["title"] == "Curated CareerMitra"
    assert updated["description"] == "Curated copy"
    assert updated["featured"] is True
    assert updated["display_order"] == 7
    assert updated["languages"] == ["Python", "TypeScript"]


@pytest.mark.asyncio
async def test_unpublish_marks_record_without_deleting_it():
    record = PortfolioPublishingService._new_record(candidate(), project(), datetime.now(timezone.utc), 1)
    db = Db(published=[record])
    result = await PortfolioPublishingService().unpublish_project(db, "7001")
    assert result["status"] == "UNPUBLISHED"
    assert len(db.published_projects.records) == 1


def test_public_endpoint_returns_only_sanitized_published_records():
    published = PortfolioPublishingService._new_record(candidate(), project(), datetime.now(timezone.utc), 1)
    published["secret_internal_note"] = "do not expose"
    published["candidate_priority"] = 99
    db = Db(published=[published, {**published, "github_repo_id": "7002", "status": "UNPUBLISHED"}])
    with patch("backend.routes.portfolio.get_database", return_value=db):
        response = TestClient(app).get("/api/portfolio/projects")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "CareerMitra"
    assert "candidate_id" not in body[0]
    assert "candidate_priority" not in body[0]
    assert "secret_internal_note" not in body[0]
    assert "approval_token" not in response.text


def test_public_endpoint_returns_empty_list_when_no_projects():
    with patch("backend.routes.portfolio.get_database", return_value=Db(published=[])):
        response = TestClient(app).get("/api/portfolio/projects")

    assert response.status_code == 200
    assert response.json() == []


def test_public_endpoint_returns_503_on_serialization_failure(caplog):
    invalid = PortfolioPublishingService._new_record(candidate(), project(), datetime.now(timezone.utc), 1)
    invalid.pop("title")
    with patch("backend.routes.portfolio.get_database", return_value=Db(published=[invalid])), caplog.at_level("ERROR"):
        response = TestClient(app).get("/api/portfolio/projects")

    assert response.status_code == 503
    assert response.json()["detail"] == "Published portfolio is unavailable"
    assert "Published portfolio serialization failed" in caplog.text


def test_public_endpoint_logs_database_exception_without_changing_safe_response(caplog):
    class FailingCollection:
        def find(self, query):
            raise RuntimeError("database connection failed")

    class FailingDb:
        published_projects = FailingCollection()

    with patch("backend.routes.portfolio.get_database", return_value=FailingDb()), caplog.at_level("ERROR"):
        response = TestClient(app).get("/api/portfolio/projects")

    assert response.status_code == 503
    assert response.json()["detail"] == "Published portfolio is unavailable"
    assert "type=RuntimeError" in caplog.text
    assert "database connection failed" in caplog.text


@pytest.mark.asyncio
async def test_approval_publishes_and_public_failure_does_not_revert_approval():
    db = Db(projects=[project()])
    db.candidates.records.append({**candidate("CANDIDATE"), "consumed_approval_token_ids": []})
    token_service = ApprovalTokenService(secret="phase7-secret")
    token = token_service.create_token("candidate-7", "APPROVE")
    result = await ApprovalService(token_service).apply(db, token)
    assert result["decision"] == "APPROVED"
    assert db.published_projects.records[0]["status"] == "PUBLISHED"
    assert db.candidates.records[0]["candidate_status"] == "APPROVED"

    failing_db = Db(projects=[project()])
    failing_db.candidates.records.append({**candidate("CANDIDATE"), "consumed_approval_token_ids": []})
    failing_db.published_projects.find_one = AsyncMock(side_effect=RuntimeError("storage unavailable"))
    failing_token = token_service.create_token("candidate-7", "APPROVE")
    failed_result = await ApprovalService(token_service).apply(failing_db, failing_token)
    assert failed_result["decision"] == "APPROVED"
    assert failing_db.candidates.records[0]["candidate_status"] == "APPROVED"
    assert failing_db.candidates.records[0]["publishing_status"] == "FAILED"
