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

        analysis = await self.ollama_service.analyze_repository(project_data, existing)

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
