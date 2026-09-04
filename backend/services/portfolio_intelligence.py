from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from backend.config import get_analysis_thresholds

logger = logging.getLogger(__name__)


class PortfolioIntelligenceService:
    def __init__(self, existing_portfolio: Optional[List[Dict[str, Any]]] = None):
        self.existing_portfolio = existing_portfolio or []

    def evaluate_project(self, project: Dict[str, Any]) -> Dict[str, Any]:
        scores = (project.get("analysis") or {}).get("scores") or {}
        overall_score = int(project.get("overall_score") or 0)
        if not overall_score and scores:
            overall_score = self._aggregate_scores(scores)

        similarity_flags = self._compute_similarity_flags(project)
        duplicate_risk = self._assess_duplicate_risk(project, similarity_flags)
        portfolio_fit_score = self._calculate_portfolio_fit(project)
        differentiation_reason = self._build_differentiation_reason(project, similarity_flags, portfolio_fit_score)
        candidate_decision = self._quality_gate(overall_score, duplicate_risk, portfolio_fit_score, project)
        candidate_priority = self._candidate_priority(overall_score, portfolio_fit_score, duplicate_risk, project)

        return {
            "project_id": project.get("github_repo_id"),
            "overall_score": overall_score,
            "duplicate_risk": duplicate_risk,
            "similarity_flags": similarity_flags,
            "portfolio_fit_score": portfolio_fit_score,
            "differentiation_reason": differentiation_reason,
            "candidate_decision": candidate_decision,
            "candidate_priority": candidate_priority,
        }

    def _compute_similarity_flags(self, project: Dict[str, Any]) -> List[str]:
        flags: List[str] = []
        project_languages = {str(item).lower() for item in (project.get("languages") or [])}
        project_topics = {str(item).lower() for item in (project.get("topics") or [])}
        project_name = (project.get("repository_name") or "").lower()

        for existing in self.existing_portfolio:
            existing_languages = {str(item).lower() for item in (existing.get("languages") or [])}
            existing_topics = {str(item).lower() for item in (existing.get("topics") or [])}
            existing_name = (existing.get("repository_name") or "").lower()

            overlap = len(project_languages & existing_languages) + len(project_topics & existing_topics)
            if project_name and project_name in existing_name:
                overlap += 5
            if project_name and existing_name and project_name == existing_name:
                overlap += 10

            if overlap >= 2:
                flags.append(f"similar_to_{existing.get('repository_name', 'existing_project')}")

        if not flags:
            return ["none"]
        return flags

    def _assess_duplicate_risk(self, project: Dict[str, Any], similarity_flags: List[str]) -> str:
        if similarity_flags == ["none"]:
            return "LOW"
        if len(similarity_flags) >= 2:
            return "HIGH"
        if len(similarity_flags) == 1:
            project_topics = {str(item).lower() for item in (project.get("topics") or [])}
            if {"ai", "chatbot"}.issubset(project_topics):
                return "HIGH"
            return "MEDIUM"
        return "LOW"

    def _calculate_portfolio_fit(self, project: Dict[str, Any]) -> int:
        scores = (project.get("analysis") or {}).get("scores") or {}
        base = scores.get("portfolio_fit", 0)
        domains = set((project.get("topics") or []))
        if domains:
            base += min(10, len(domains) * 2)
        return max(0, min(100, int(base)))

    def _build_differentiation_reason(self, project: Dict[str, Any], similarity_flags: List[str], portfolio_fit_score: int) -> str:
        if similarity_flags == ["none"]:
            return "This project adds a distinct capability and helps diversify the portfolio."
        if portfolio_fit_score >= 75:
            return "This project is differentiated enough to add value despite some overlap with the existing portfolio."
        return "This project overlaps materially with the current portfolio and should be reviewed before promotion."

    def _quality_gate(self, overall_score: int, duplicate_risk: str, portfolio_fit_score: int, project: Dict[str, Any]) -> str:
        threshold = get_analysis_thresholds()
        ignore_max = int(threshold.get("ignore_max", 64))
        candidate_min = int(threshold.get("candidate_min", 85))

        if overall_score < ignore_max:
            return "IGNORE"
        if duplicate_risk == "HIGH":
            return "REVIEW"
        if duplicate_risk == "MEDIUM" and portfolio_fit_score < 70:
            return "REVIEW"
        if overall_score >= 80 and duplicate_risk in {"LOW", "MEDIUM"} and portfolio_fit_score >= 75:
            return "CANDIDATE"
        if overall_score >= candidate_min and duplicate_risk == "LOW":
            return "CANDIDATE"
        if overall_score >= 65:
            return "REVIEW"
        return "IGNORE"

    def _candidate_priority(self, overall_score: int, portfolio_fit_score: int, duplicate_risk: str, project: Dict[str, Any]) -> int:
        evidence_strength = len((project.get("analysis") or {}).get("evidence") or []) * 8
        maturity = ((project.get("analysis") or {}).get("scores") or {}).get("maturity", 0)
        duplication_penalty = {"LOW": 0, "MEDIUM": 10, "HIGH": 25}.get(duplicate_risk, 0)
        total = overall_score + portfolio_fit_score + evidence_strength + maturity - duplication_penalty
        return max(0, min(100, int(total / 1.5)))

    @staticmethod
    def _aggregate_scores(scores: Dict[str, Any]) -> int:
        weighted = {
            "technical_depth": 0.20,
            "complexity": 0.15,
            "originality": 0.15,
            "impact": 0.15,
            "engineering_quality": 0.15,
            "maturity": 0.10,
            "collaboration": 0.05,
            "portfolio_fit": 0.05,
        }
        total = 0.0
        weight_total = 0.0
        for key, weight in weighted.items():
            value = max(0, min(100, int(scores.get(key, 0))))
            total += value * weight
            weight_total += weight
        if weight_total == 0:
            return 0
        return max(0, min(100, int(round(total / weight_total))))
