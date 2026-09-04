from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.models.candidate import CandidateRecord
from backend.server import app
from backend.services.candidate_service import CandidateService
from backend.services.portfolio_intelligence import PortfolioIntelligenceService


@pytest.fixture
def strong_project():
    return {
        "github_repo_id": "9001",
        "owner": "pratham",
        "repository_name": "PortfolioAssistant",
        "full_name": "pratham/PortfolioAssistant",
        "description": "AI-driven portfolio evaluation and candidate pipeline",
        "github_url": "https://github.com/pratham/PortfolioAssistant",
        "languages": ["Python", "TypeScript"],
        "topics": ["ai", "portfolio", "automation", "fastapi"],
        "stars": 120,
        "forks": 22,
        "contributors": ["pratham", "alice", "bob"],
        "created_at": datetime(2024, 1, 15, tzinfo=timezone.utc),
        "updated_at": datetime(2025, 4, 1, tzinfo=timezone.utc),
        "analysis": {
            "summary": "Strong productized system with AI workflow and backend architecture.",
            "scores": {
                "technical_depth": 88,
                "complexity": 82,
                "originality": 85,
                "impact": 80,
                "engineering_quality": 86,
                "maturity": 78,
                "collaboration": 72,
                "portfolio_fit": 90,
            },
            "evidence": ["Repository contains FastAPI app and React frontend", "Multiple contributors and active GitHub metadata"],
            "recommendation": "CANDIDATE",
        },
        "overall_score": 84,
        "recommendation": "CANDIDATE",
        "analysis_status": "ANALYZED",
        "portfolio_status": "DISCOVERED",
    }


@pytest.fixture
def weak_project():
    return {
        "github_repo_id": "9002",
        "owner": "pratham",
        "repository_name": "TodoClone",
        "full_name": "pratham/TodoClone",
        "description": "A basic todo list app",
        "github_url": "https://github.com/pratham/TodoClone",
        "languages": ["JavaScript"],
        "topics": ["todo", "crud"],
        "stars": 2,
        "forks": 0,
        "contributors": ["pratham"],
        "created_at": datetime(2025, 1, 1, tzinfo=timezone.utc),
        "updated_at": datetime(2025, 1, 5, tzinfo=timezone.utc),
        "analysis": {
            "summary": "Very small CRUD app with limited complexity.",
            "scores": {
                "technical_depth": 30,
                "complexity": 25,
                "originality": 20,
                "impact": 25,
                "engineering_quality": 35,
                "maturity": 30,
                "collaboration": 15,
                "portfolio_fit": 20,
            },
            "evidence": ["Minimal repository with no significant architecture evidence"],
            "recommendation": "IGNORE",
        },
        "overall_score": 25,
        "recommendation": "IGNORE",
        "analysis_status": "ANALYZED",
        "portfolio_status": "DISCOVERED",
    }


@pytest.fixture
def existing_portfolio():
    return [
        {
            "github_repo_id": "100",
            "repository_name": "ChatbotStudio",
            "full_name": "pratham/ChatbotStudio",
            "languages": ["Python"],
            "topics": ["ai", "chatbot"],
            "analysis": {"overall_score": 80},
            "portfolio_status": "FEATURED",
        },
        {
            "github_repo_id": "101",
            "repository_name": "TaskManager",
            "full_name": "pratham/TaskManager",
            "languages": ["JavaScript"],
            "topics": ["crud"],
            "analysis": {"overall_score": 72},
            "portfolio_status": "FEATURED",
        },
    ]


def test_high_quality_project_becomes_candidate(strong_project, existing_portfolio):
    portfolio = PortfolioIntelligenceService(existing_portfolio)
    decision = portfolio.evaluate_project(strong_project)

    assert decision["candidate_decision"] == "CANDIDATE"
    assert decision["portfolio_fit_score"] >= 0
    assert decision["duplicate_risk"] in {"LOW", "MEDIUM", "HIGH"}


def test_low_quality_project_becomes_ignored(weak_project, existing_portfolio):
    portfolio = PortfolioIntelligenceService(existing_portfolio)
    decision = portfolio.evaluate_project(weak_project)

    assert decision["candidate_decision"] == "IGNORE"
    assert decision["overall_score"] <= 64


def test_high_duplicate_risk_prevents_automatic_candidate_promotion(strong_project, existing_portfolio):
    duplicate_project = {
        **strong_project,
        "github_repo_id": "9003",
        "repository_name": "AIChatbotLite",
        "full_name": "pratham/AIChatbotLite",
        "topics": ["ai", "chatbot"],
        "languages": ["Python"],
        "analysis": {**strong_project["analysis"], "scores": {**strong_project["analysis"]["scores"], "originality": 35, "portfolio_fit": 30}},
    }

    portfolio = PortfolioIntelligenceService(existing_portfolio)
    decision = portfolio.evaluate_project(duplicate_project)

    assert decision["duplicate_risk"] == "HIGH"
    assert decision["candidate_decision"] in {"IGNORE", "REVIEW"}


def test_portfolio_differentiation_is_calculated(strong_project, existing_portfolio):
    portfolio = PortfolioIntelligenceService(existing_portfolio)
    decision = portfolio.evaluate_project(strong_project)

    assert "similarity_flags" in decision
    assert "differentiation_reason" in decision
    assert isinstance(decision["portfolio_fit_score"], (int, float))


def test_candidate_priority_calculation(strong_project, existing_portfolio):
    portfolio = PortfolioIntelligenceService(existing_portfolio)
    decision = portfolio.evaluate_project(strong_project)

    assert "candidate_priority" in decision
    assert 0 <= decision["candidate_priority"] <= 100


def test_duplicate_candidate_prevention():
    service = CandidateService()
    existing = {
        "candidate_id": "candidate-123",
        "github_repo_id": "9001",
        "project_id": "9001",
        "candidate_status": "CANDIDATE",
        "recommendation": "CANDIDATE",
        "overall_score": 82,
        "analysis_version": "phase2-v1",
    }

    result = service.upsert_candidate(existing, {"candidate_status": "CANDIDATE", "overall_score": 88})

    assert result["candidate_id"] == "candidate-123"
    assert result["overall_score"] == 88


def test_candidate_re_evaluation_updates_existing_record():
    service = CandidateService()

    existing = {
        "candidate_id": "candidate-456",
        "github_repo_id": "9007",
        "project_id": "9007",
        "candidate_status": "CANDIDATE",
        "recommendation": "REVIEW",
        "overall_score": 72,
        "analysis_version": "phase2-v1",
    }

    updated = service.upsert_candidate(existing, {"candidate_status": "CANDIDATE", "overall_score": 88, "recommendation": "CANDIDATE", "reviewed_at": datetime.now(timezone.utc)})

    assert updated["candidate_id"] == "candidate-456"
    assert updated["overall_score"] == 88
    assert updated["recommendation"] == "CANDIDATE"


def test_candidate_retrieval_and_status_filtering():
    service = CandidateService()
    items = [
        {"candidate_id": "candidate-a", "github_repo_id": "1", "candidate_status": "CANDIDATE", "recommendation": "CANDIDATE"},
        {"candidate_id": "candidate-b", "github_repo_id": "2", "candidate_status": "REJECTED", "recommendation": "IGNORE"},
    ]

    candidates = service.filter_candidates(items, "CANDIDATE")
    assert [item["candidate_id"] for item in candidates] == ["candidate-a"]


def test_evaluate_endpoint_creates_candidate_on_quality_gate(strong_project):
    fake_db = MagicMock()
    fake_db.projects = MagicMock()
    fake_db.projects.find_one = AsyncMock(return_value={**strong_project, "analysis": strong_project["analysis"], "analysis_status": "ANALYZED"})
    fake_db.projects.update_one = AsyncMock(return_value=None)
    fake_db.projects.find = AsyncMock(return_value=[])
    fake_db.candidates = MagicMock()
    fake_db.candidates.find_one = AsyncMock(return_value=None)
    fake_db.candidates.update_one = AsyncMock(return_value=None)
    fake_db.candidates.insert_one = AsyncMock(return_value=None)

    with patch("backend.routes.projects.get_database", return_value=fake_db):
        client = TestClient(app)
        response = client.post("/api/projects/9001/evaluate")
        assert response.status_code == 200
        payload = response.json()
        assert payload["candidate_decision"] == "CANDIDATE"
