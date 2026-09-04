from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.server import app
from backend.services.portfolio_ranking import PortfolioRankingService


def project(repo_id, title, topics, score=90, **extra):
    return {
        "github_repo_id": repo_id,
        "title": title,
        "description": f"A {title} project",
        "languages": ["Python"],
        "technologies": ["FastAPI"],
        "topics": topics,
        "category": "Software Project",
        "status": "PUBLISHED",
        "overall_score": score,
        "display_order": int(repo_id),
        "featured": extra.pop("featured", False),
        **extra,
    }


def test_ranking_is_deterministic_and_high_quality_wins():
    projects = [project("1", "Strong", ["backend", "automation"], 96), project("2", "Basic", ["web"], 58)]
    service = PortfolioRankingService()
    first = service.rank_portfolio(projects)
    second = service.rank_portfolio(projects)
    assert first == second
    assert first["ranked_projects"][0]["title"] == "Strong"
    assert first["ranked_projects"][0]["rank"] == 1


def test_diversity_and_similarity_signals_are_reported():
    items = [project("1", "AI One", ["ai", "chatbot"]), project("2", "AI Two", ["ai", "chatbot"]), project("3", "Systems", ["systems", "distributed"])]
    result = PortfolioRankingService().rank_portfolio(items)
    ai = next(item for item in result["ranked_projects"] if item["title"] == "AI Two")
    systems = next(item for item in result["ranked_projects"] if item["title"] == "Systems")
    assert ai["similarity_score"] > 0
    assert ai["similarity_penalty"] > 0
    assert systems["diversity_score"] >= ai["diversity_score"]
    assert "AI / ML" in ai["domains"]
    assert "Systems" in systems["domains"]


def test_diminishing_returns_and_manual_overrides():
    items = [
        project("1", "AI One", ["ai", "chatbot"], 94, featured=True, manually_featured=True),
        project("2", "AI Two", ["ai", "chatbot"], 93),
        project("3", "AI Three", ["ai", "chatbot"], 92),
        project("4", "Curated", ["systems"], 80, manual_rank=1, manual_featured=True, featured=True),
    ]
    ranked = PortfolioRankingService().rank_portfolio(items)
    ai_scores = [item["ranking_score"] for item in ranked["ranked_projects"] if item["title"].startswith("AI")]
    assert ai_scores[0] >= ai_scores[1] >= ai_scores[2]
    curated = next(item for item in ranked["ranked_projects"] if item["title"] == "Curated")
    assert curated["recommended_rank"] == 1
    assert curated["recommended_featured"] is True
    assert ranked["max_featured_projects"] == 6


def test_rejected_and_ignored_projects_are_excluded():
    items = [project("1", "Published", ["backend"]), project("2", "Rejected", ["ai"], status="REJECTED"), project("3", "Ignored", ["web"], status="IGNORE")]
    result = PortfolioRankingService().rank_portfolio(items)
    assert [item["title"] for item in result["ranked_projects"]] == ["Published"]
    assert result["excluded_project_count"] == 2


def test_health_and_gap_detection():
    result = PortfolioRankingService().portfolio_health([project("1", "Web", ["web"], 88), project("2", "Web 2", ["web"], 84)])
    assert 0 <= result["health_score"] <= 100
    assert "breadth_score" in result
    assert "No mobile project is represented." in result["recommendations"]
    assert "No systems project is represented." in result["recommendations"]
    assert any("web development" in item.lower() for item in result["recommendations"])


class Cursor:
    def __init__(self, records):
        self.records = records

    def sort(self, field, direction):
        self.records.sort(key=lambda item: item.get(field, 0), reverse=direction < 0)
        return self

    async def to_list(self, length=500):
        return self.records[:length]


class Collection:
    def __init__(self, records):
        self.records = records

    def find(self, query):
        return Cursor([item for item in self.records if all(item.get(key) == value for key, value in query.items())])


class Db:
    def __init__(self, records):
        self.published_projects = Collection(records)
        self.candidates = Collection([])


def test_ranking_and_health_endpoints():
    records = [project("1", "Public Project", ["backend"], 91)]
    with patch("backend.routes.portfolio.get_database", return_value=Db(records)):
        client = TestClient(app)
        ranking = client.get("/api/portfolio/ranking")
        health = client.get("/api/portfolio/health")
    assert ranking.status_code == 200
    assert ranking.json()["ranked_projects"][0]["title"] == "Public Project"
    assert health.status_code == 200
    assert "health_score" in health.json()
    assert "approval_token" not in ranking.text
    assert "secret" not in ranking.text.lower()
