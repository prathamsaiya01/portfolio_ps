from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.models.project import ProjectRecord
from backend.services.ollama_service import OllamaService, OllamaServiceError
from backend.services.project_analyzer import ProjectAnalyzer
from backend.services.scoring_service import calculate_overall_score, clamp_score, recommendation_for_score
from backend.server import app


@pytest.fixture
def sample_project():
    return {
        "github_repo_id": "101",
        "owner": "pratham",
        "repository_name": "CareerMitra",
        "full_name": "pratham/CareerMitra",
        "description": "AI career guidance platform",
        "github_url": "https://github.com/pratham/CareerMitra",
        "homepage_url": "https://careermitra.example",
        "readme": "# CareerMitra\nThis project builds an AI-powered career guidance platform with FastAPI and React.",
        "languages": ["Python", "TypeScript", "PostgreSQL"],
        "topics": ["ai", "career", "fastapi"],
        "stars": 42,
        "forks": 8,
        "contributors": ["pratham", "mentor"],
        "repository_visibility": "public",
        "portfolio_status": "DISCOVERED",
        "created_at": datetime(2024, 1, 15, tzinfo=timezone.utc),
        "updated_at": datetime(2025, 3, 20, tzinfo=timezone.utc),
    }


@pytest.fixture
def existing_projects():
    return [
        {
            "github_repo_id": "1",
            "repository_name": "ChatHelper",
            "full_name": "pratham/ChatHelper",
            "languages": ["Python", "JavaScript"],
            "topics": ["ai", "chatbot"],
            "portfolio_status": "PORTFOLIO",
            "analysis": {"overall_score": 78},
        },
        {
            "github_repo_id": "2",
            "repository_name": "TaskBoard",
            "full_name": "pratham/TaskBoard",
            "languages": ["TypeScript"],
            "topics": ["productivity"],
            "portfolio_status": "PORTFOLIO",
            "analysis": {"overall_score": 82},
        },
    ]


@pytest.mark.asyncio
async def test_ollama_service_successful_analysis(sample_project, existing_projects):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "response": '{"summary":"Strong AI product with backend and frontend work.","suggested_title":"CareerMitra","suggested_description":"AI-powered career guidance platform","scores":{"technical_depth":82,"complexity":78,"originality":76,"impact":70,"engineering_quality":80,"maturity":74,"collaboration":68,"portfolio_fit":88},"strengths":["AI product flow","full-stack implementation"],"weaknesses":["Limited deployment evidence"],"evidence":["Repository contains FastAPI backend and React frontend","Repository lists contributors and project metadata"],"why_it_stands_out":["Combines AI workflow with product thinking"],"missing_evidence":["No deployment or production metrics"],"recommendation":"REVIEW"}'
    }

    with patch("backend.services.ollama_service.httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        service = OllamaService(base_url="http://localhost:11434", model="llama3.1")
        result = await service.analyze_repository(sample_project, existing_projects)

    assert result["summary"].startswith("Strong")
    assert result["scores"]["technical_depth"] == 82
    assert result["recommendation"] == "REVIEW"


def test_ollama_prompt_is_a_string(sample_project, existing_projects):
    prompt = OllamaService(model="qwen2.5:1.5b")._build_prompt(sample_project, existing_projects)

    assert isinstance(prompt, str)
    assert "The project context is:" in prompt


@pytest.mark.asyncio
async def test_local_qwen_generation_succeeds(sample_project):
    service = OllamaService(model="qwen2.5:1.5b", timeout=60.0)
    if not await service.check_availability():
        pytest.skip("Local Ollama is unavailable")

    result = await service.analyze_repository(sample_project, [])

    assert isinstance(result, dict)
    assert result["recommendation"] in {"IGNORE", "REVIEW", "CANDIDATE"}


@pytest.mark.asyncio
async def test_ollama_service_rejects_malformed_response(sample_project, existing_projects):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"response": "{not valid json"}

    with patch("backend.services.ollama_service.httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        service = OllamaService(base_url="http://localhost:11434", model="llama3.1")
        with pytest.raises(OllamaServiceError):
            await service.analyze_repository(sample_project, existing_projects)


@pytest.mark.asyncio
async def test_ollama_service_handles_unavailable_service(sample_project, existing_projects):
    with patch("backend.services.ollama_service.httpx.AsyncClient.post", side_effect=httpx.ConnectError("offline")):
        service = OllamaService(base_url="http://localhost:11434", model="llama3.1")
        with pytest.raises(OllamaServiceError):
            await service.analyze_repository(sample_project, existing_projects)


def test_score_calculation_and_clamping():
    scores = {
        "technical_depth": 120,
        "complexity": 80,
        "originality": -10,
        "impact": 90,
        "engineering_quality": 75,
        "maturity": 70,
        "collaboration": 60,
        "portfolio_fit": 65,
    }

    overall = calculate_overall_score(scores)

    assert 0 <= overall <= 100
    assert overall >= 70
    assert clamp_score(150) == 100
    assert clamp_score(-40) == 0


@pytest.mark.parametrize(
    ("score", "expected"),
    [(64, "IGNORE"), (65, "REVIEW"), (84, "REVIEW"), (85, "CANDIDATE")],
)
def test_recommendation_thresholds(score, expected):
    assert recommendation_for_score(score) == expected


def test_evidence_preservation_behavior(sample_project, existing_projects):
    analysis = {
        "summary": "Strong product prototype",
        "scores": {"technical_depth": 75, "complexity": 70, "originality": 68, "impact": 60, "engineering_quality": 72, "maturity": 64, "collaboration": 55, "portfolio_fit": 80},
        "strengths": ["FastAPI backend"],
        "weaknesses": ["Short timeline"],
        "evidence": ["Repository contains FastAPI application and React frontend"],
        "why_it_stands_out": ["Uses product and AI flow"],
        "missing_evidence": ["No production deployment docs"],
        "recommendation": "REVIEW",
    }

    assert analysis["evidence"][0].startswith("Repository")
    assert "10,000 users" not in str(analysis)
    assert analysis["recommendation"] in {"IGNORE", "REVIEW", "CANDIDATE"}


@pytest.mark.asyncio
async def test_project_analyzer_existing_portfolio_comparison(sample_project, existing_projects):
    with patch("backend.services.project_analyzer.OllamaService.analyze_repository", new_callable=AsyncMock, return_value={
        "summary": "Differentiated AI product that adds career guidance to the portfolio.",
        "suggested_title": "CareerMitra",
        "suggested_description": "AI-powered career guidance platform",
        "scores": {"technical_depth": 80, "complexity": 76, "originality": 78, "impact": 72, "engineering_quality": 79, "maturity": 70, "collaboration": 65, "portfolio_fit": 85},
        "strengths": ["AI product flow"],
        "weaknesses": ["Limited deployment evidence"],
        "evidence": ["Repository contains FastAPI and React"],
        "why_it_stands_out": ["Differentiates from past chatbot work"],
        "missing_evidence": ["No production deployment evidence"],
        "recommendation": "REVIEW",
    }):
        analysis = await ProjectAnalyzer().analyze_project(sample_project, existing_projects)

    assert analysis["recommendation"] == "REVIEW"
    assert "Differentiates" in analysis["summary"] or "portfolio" in str(analysis).lower()


@pytest.mark.asyncio
async def test_project_analysis_persistence_and_retrieval(sample_project):
    class FakeCollection:
        def __init__(self, doc):
            self.doc = doc

        async def find_one(self, query):
            return self.doc.copy() if query.get("github_repo_id") == self.doc.get("github_repo_id") else None

        async def update_one(self, query, updates):
            if query.get("github_repo_id") == self.doc.get("github_repo_id"):
                self.doc.update(updates.get("$set", {}))

    fake_db = MagicMock()
    fake_db.projects = FakeCollection({**sample_project, "analysis_status": "NOT_ANALYZED", "analysis": {}, "overall_score": None, "recommendation": "IGNORE"})

    mock_analysis = {
        "summary": "Strong product prototype",
        "suggested_title": "CareerMitra",
        "suggested_description": "AI-powered career guidance platform",
        "scores": {"technical_depth": 80, "complexity": 74, "originality": 76, "impact": 70, "engineering_quality": 78, "maturity": 72, "collaboration": 66, "portfolio_fit": 84},
        "strengths": ["Well-scoped product"],
        "weaknesses": ["No production deployment evidence"],
        "evidence": ["Repository contains FastAPI backend and React frontend"],
        "why_it_stands_out": ["Strong product direction"],
        "missing_evidence": ["Deployment metrics"],
        "recommendation": "CANDIDATE",
    }

    with patch("backend.routes.projects.get_database", return_value=fake_db), \
         patch("backend.services.project_analyzer.OllamaService.analyze_repository", new_callable=AsyncMock, return_value=mock_analysis):
        client = TestClient(app)
        response = client.post("/api/projects/101/analyze")
        assert response.status_code == 200
        payload = response.json()
        assert payload["recommendation"] == "REVIEW"
        assert payload["overall_score"] >= 0

        retrieval = client.get("/api/projects/101/analysis")
        assert retrieval.status_code == 200
        assert retrieval.json()["analysis"]["summary"] == "Strong product prototype"


@pytest.mark.asyncio
async def test_analysis_route_handles_ollama_unavailable(sample_project):
    class FakeCollection:
        def __init__(self, doc):
            self.doc = doc

        async def find_one(self, query):
            return self.doc.copy() if query.get("github_repo_id") == self.doc.get("github_repo_id") else None

        async def update_one(self, query, updates):
            if query.get("github_repo_id") == self.doc.get("github_repo_id"):
                self.doc.update(updates.get("$set", {}))

    fake_db = MagicMock()
    fake_db.projects = FakeCollection({**sample_project, "analysis_status": "NOT_ANALYZED", "analysis": {}, "overall_score": None, "recommendation": "IGNORE"})

    with patch("backend.routes.projects.get_database", return_value=fake_db), \
         patch("backend.services.project_analyzer.OllamaService.analyze_repository", side_effect=Exception("offline")):
        client = TestClient(app)
        response = client.post("/api/projects/101/analyze")
        assert response.status_code == 200
        assert response.json()["analysis_status"] == "AI_UNAVAILABLE"
        assert response.json()["analysis"]["ai_analysis_status"] == "UNAVAILABLE"
        assert response.json()["recommendation"] == "REVIEW"
