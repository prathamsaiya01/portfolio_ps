from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

import httpx

from backend.config import get_settings

logger = logging.getLogger(__name__)


class OllamaServiceError(RuntimeError):
    pass


class OllamaService:
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None, timeout: float = 120.0):
        settings = get_settings()
        self.base_url = (base_url or settings.get("ollama_base_url") or "http://localhost:11434").rstrip("/")
        self.model = model or settings.get("ollama_model")
        self.timeout = timeout

    async def check_availability(self) -> bool:
        if not self.base_url:
            return False
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                return response.status_code == 200
        except (httpx.HTTPError, ValueError, TypeError):
            return False

    async def analyze_repository(self, project: Dict[str, Any], existing_projects: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        if not self.model:
            raise OllamaServiceError("Ollama model is not configured.")

        project_context = project or {}
        portfolio_context = existing_projects or []

        prompt = self._build_prompt(project_context, portfolio_context)
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1},
            "format": "json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                body = response.json()
        except httpx.TimeoutException as exc:
            raise OllamaServiceError("Ollama request timed out.") from exc
        except httpx.HTTPError as exc:
            raise OllamaServiceError(f"Ollama service is unavailable: {exc}") from exc
        except ValueError as exc:
            raise OllamaServiceError("Malformed Ollama response received.") from exc

        raw_content = (body or {}).get("response")
        if not raw_content or not isinstance(raw_content, str):
            raise OllamaServiceError("Ollama returned an empty or malformed response.")

        try:
            parsed = json.loads(raw_content)
        except json.JSONDecodeError as exc:
            raise OllamaServiceError("Ollama response was not valid JSON.") from exc

        if not isinstance(parsed, dict):
            raise OllamaServiceError("Ollama response did not contain a JSON object.")

        return self._normalize_analysis(parsed)

    def _build_prompt(self, project: Dict[str, Any], existing_projects: List[Dict[str, Any]]) -> str:
        evidence = project.get("readme") or ""
        summary_context = {
            "project_name": project.get("full_name") or project.get("repository_name") or "Unknown",
            "description": project.get("description") or "",
            "languages": project.get("languages") or [],
            "topics": project.get("topics") or [],
            "stars": project.get("stars"),
            "forks": project.get("forks"),
            "contributors": project.get("contributors") or [],
            "homepage": project.get("homepage_url") or "",
            "readme_excerpt": (evidence[:2000] if isinstance(evidence, str) else ""),
            "repository_visibility": project.get("repository_visibility") or "public",
            "existing_projects": [
                {
                    "name": item.get("full_name") or item.get("repository_name") or "Unknown",
                    "languages": item.get("languages") or [],
                    "topics": item.get("topics") or [],
                    "analysis": item.get("analysis") or {"overall_score": item.get("overall_score")},
                }
                for item in existing_projects[:10]
            ],
        }

        return "".join((
            "You are evaluating a GitHub repository for a portfolio.",
            "\nUse only repository evidence. Do not fabricate facts.",
            "\nIf evidence is unavailable, say evidence is unavailable.",
            "\nDo not invent users, revenue, performance numbers, achievements, technologies, deployment claims, awards, or impact metrics.",
            "\nReturn valid JSON only with the following fields: summary, suggested_title, suggested_description, scores, overall_score, strengths, weaknesses, evidence, why_it_stands_out, missing_evidence, recommendation.",
            "\nThe scores object must include technical_depth, complexity, originality, impact, engineering_quality, maturity, collaboration, portfolio_fit as integers from 0 to 100.",
            "\nRecommendation must be one of IGNORE, REVIEW, or CANDIDATE.",
            "\nThe project context is: " + json.dumps(summary_context, ensure_ascii=True)
        ))

    def _normalize_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        scores = analysis.get("scores") or {}
        normalized_scores = {
            "technical_depth": self._coerce_score(scores.get("technical_depth")),
            "complexity": self._coerce_score(scores.get("complexity")),
            "originality": self._coerce_score(scores.get("originality")),
            "impact": self._coerce_score(scores.get("impact")),
            "engineering_quality": self._coerce_score(scores.get("engineering_quality")),
            "maturity": self._coerce_score(scores.get("maturity")),
            "collaboration": self._coerce_score(scores.get("collaboration")),
            "portfolio_fit": self._coerce_score(scores.get("portfolio_fit")),
        }

        normalized = {
            "summary": str(analysis.get("summary") or "Evidence review unavailable."),
            "suggested_title": str(analysis.get("suggested_title") or "Project"),
            "suggested_description": str(analysis.get("suggested_description") or "Repository evidence supports a software project."),
            "scores": normalized_scores,
            "overall_score": self._coerce_score(analysis.get("overall_score")),
            "strengths": [str(item) for item in (analysis.get("strengths") or [])],
            "weaknesses": [str(item) for item in (analysis.get("weaknesses") or [])],
            "evidence": [str(item) for item in (analysis.get("evidence") or [])],
            "why_it_stands_out": [str(item) for item in (analysis.get("why_it_stands_out") or [])],
            "missing_evidence": [str(item) for item in (analysis.get("missing_evidence") or [])],
            "recommendation": str(analysis.get("recommendation") or "REVIEW").upper(),
        }

        if normalized["recommendation"] not in {"IGNORE", "REVIEW", "CANDIDATE"}:
            normalized["recommendation"] = "REVIEW"

        for key in normalized["scores"]:
            normalized["scores"][key] = max(0, min(100, int(normalized["scores"][key])))

        if normalized["overall_score"] <= 0:
            from backend.services.scoring_service import calculate_overall_score
            normalized["overall_score"] = calculate_overall_score(normalized["scores"])

        normalized["recommendation"] = str(normalized["recommendation"]).upper()
        return normalized

    @staticmethod
    def _coerce_score(value: Any) -> int:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return 0
        return max(0, min(100, int(round(numeric))))
