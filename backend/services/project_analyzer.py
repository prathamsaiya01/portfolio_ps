from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from backend.services.ollama_service import OllamaService
from backend.services.scoring_service import calculate_overall_score, recommendation_for_score

logger = logging.getLogger(__name__)


class ProjectAnalyzer:
    def __init__(self, ollama_service: Optional[OllamaService] = None):
        self.ollama_service = ollama_service or OllamaService()

    async def analyze_project(self, project: Dict[str, Any], existing_projects: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        project_data = project.copy() if isinstance(project, dict) else dict(project)
        existing = existing_projects or []

        try:
            analysis = await self.ollama_service.analyze_repository(project_data, existing)
        except Exception as exc:
            logger.warning("Ollama advisory analysis unavailable: %s", type(exc).__name__)
            return {
                "summary": "AI analysis is unavailable. Repository facts are preserved for human review.",
                "suggested_title": project_data.get("repository_name") or "Project",
                "suggested_description": project_data.get("description") or "Repository description is available for human review.",
                "scores": {},
                "overall_score": 0,
                "strengths": [],
                "weaknesses": ["AI analysis unavailable"],
                "evidence": ["GitHub repository metadata was collected successfully."],
                "why_it_stands_out": [],
                "missing_evidence": ["AI analysis unavailable"],
                "recommendation": "REVIEW",
                "ai_analysis_status": "UNAVAILABLE",
                "ai_analysis_error": type(exc).__name__,
            }

        scores = analysis.get("scores") or {}
        overall_score = calculate_overall_score(scores)
        recommendation = recommendation_for_score(overall_score)

        analysis["overall_score"] = overall_score
        analysis["recommendation"] = recommendation

        if not analysis.get("summary"):
            analysis["summary"] = "Evidence is limited, so this repository requires additional validation before portfolio consideration."
        if not analysis.get("evidence"):
            analysis["evidence"] = ["No direct repository evidence was available for a confident assessment."]

        return analysis
