from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from backend.services.portfolio_intelligence import PortfolioIntelligenceService
from backend.services.project_analyzer import ProjectAnalyzer
from backend.services.ollama_service import OllamaService, OllamaServiceError


def test_ollama_default_timeout_is_120_seconds():
    assert OllamaService(model="qwen2.5:1.5b").timeout == 120.0


@pytest.mark.asyncio
async def test_ollama_timeout_produces_unavailable_fallback():
    project = {"github_repo_id": "timeout-1", "repository_name": "TimeoutProject", "description": "Facts remain available."}
    timeout = httpx.ReadTimeout("ollama timeout")
    mock_response = MagicMock()

    with patch("backend.services.ollama_service.httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=timeout):
        analysis = await ProjectAnalyzer(OllamaService(model="qwen2.5:1.5b")).analyze_project(project)

    assert analysis["ai_analysis_status"] == "UNAVAILABLE"
    assert analysis["recommendation"] == "REVIEW"
    assert analysis["evidence"]


@pytest.mark.asyncio
async def test_ollama_failure_preserves_repository_for_review():
    project = {
        "github_repo_id": "optional-1",
        "repository_name": "KnownProject",
        "description": "A collected GitHub project",
        "languages": ["Python"],
        "contribution_evidence": {"meaningful_contribution": True},
    }
    ollama = AsyncMock()
    ollama.analyze_repository.side_effect = OllamaServiceError("offline")

    analysis = await ProjectAnalyzer(ollama_service=ollama).analyze_project(project)
    project["analysis"] = analysis
    decision = PortfolioIntelligenceService([]).evaluate_project(project)

    assert analysis["ai_analysis_status"] == "UNAVAILABLE"
    assert analysis["evidence"]
    assert decision["candidate_decision"] == "REVIEW"


def test_approval_is_still_required_before_publishing():
    service = PortfolioIntelligenceService([])
    project = {
        "github_repo_id": "optional-2",
        "repository_name": "ReviewProject",
        "analysis": {"ai_analysis_status": "UNAVAILABLE", "scores": {}},
        "overall_score": 0,
    }

    decision = service.evaluate_project(project)

    assert decision["candidate_decision"] == "REVIEW"
