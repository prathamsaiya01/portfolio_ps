from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class CandidateService:
    def __init__(self):
        pass

    def upsert_candidate(self, existing: Optional[Dict[str, Any]], payload: Dict[str, Any]) -> Dict[str, Any]:
        if existing and existing.get("candidate_id"):
            merged = dict(existing)
            merged.update(payload)
            merged["updated_at"] = payload.get("updated_at") or datetime.now(timezone.utc)
            if payload.get("reviewed_at"):
                merged["reviewed_at"] = payload["reviewed_at"]
            return merged

        candidate_id = payload.get("candidate_id") or f"candidate-{uuid.uuid4().hex}"
        new_candidate = {
            "candidate_id": candidate_id,
            "github_repo_id": payload.get("github_repo_id"),
            "project_id": payload.get("project_id"),
            "full_name": payload.get("full_name", ""),
            "owner": payload.get("owner", ""),
            "description": payload.get("description"),
            "github_url": payload.get("github_url"),
            "collaborators": payload.get("collaborators") or [],
            "repository_name": payload.get("repository_name"),
            "repository_url": payload.get("repository_url"),
            "candidate_status": payload.get("candidate_status", "DISCOVERED"),
            "recommendation": payload.get("recommendation", "REVIEW"),
            "overall_score": payload.get("overall_score"),
            "analysis_version": payload.get("analysis_version", "phase2-v1"),
            "suggested_title": payload.get("suggested_title"),
            "suggested_description": payload.get("suggested_description"),
            "strengths": payload.get("strengths") or [],
            "weaknesses": payload.get("weaknesses") or [],
            "evidence": payload.get("evidence") or [],
            "why_it_stands_out": payload.get("why_it_stands_out") or [],
            "missing_evidence": payload.get("missing_evidence") or [],
            "created_at": payload.get("created_at") or datetime.now(timezone.utc),
            "updated_at": payload.get("updated_at") or datetime.now(timezone.utc),
            "reviewed_at": payload.get("reviewed_at"),
            "rejection_reason": payload.get("rejection_reason"),
            "candidate_priority": payload.get("candidate_priority"),
            "duplicate_risk": payload.get("duplicate_risk"),
            "portfolio_fit_score": payload.get("portfolio_fit_score"),
            "similarity_flags": payload.get("similarity_flags") or [],
            "differentiation_reason": payload.get("differentiation_reason"),
            "scores": payload.get("scores") or {},
            "contribution_evidence": payload.get("contribution_evidence") or {},
        }
        return new_candidate

    def filter_candidates(self, items: List[Dict[str, Any]], status: str) -> List[Dict[str, Any]]:
        desired = (status or "").upper()
        return [item for item in items if str(item.get("candidate_status") or "").upper() == desired]

    @staticmethod
    def normalize_decision(project: Dict[str, Any], portfolio_decision: Dict[str, Any]) -> Dict[str, Any]:
        recommendation = str(project.get("recommendation") or portfolio_decision.get("candidate_decision", "IGNORE")).upper()
        if recommendation not in {"IGNORE", "REVIEW", "CANDIDATE"}:
            recommendation = "REVIEW"
        return {
            "candidate_status": "CANDIDATE" if recommendation == "CANDIDATE" else "REJECTED" if recommendation == "IGNORE" else "CANDIDATE",
            "recommendation": recommendation,
            "overall_score": portfolio_decision.get("overall_score"),
            "analysis_version": project.get("analysis_version", "phase2-v1"),
            "suggested_title": (project.get("analysis") or {}).get("suggested_title") or project.get("repository_name"),
            "suggested_description": (project.get("analysis") or {}).get("suggested_description") or project.get("description"),
            "strengths": (project.get("analysis") or {}).get("strengths") or [],
            "weaknesses": (project.get("analysis") or {}).get("weaknesses") or [],
            "evidence": (project.get("analysis") or {}).get("evidence") or [],
            "why_it_stands_out": (project.get("analysis") or {}).get("why_it_stands_out") or [],
            "missing_evidence": (project.get("analysis") or {}).get("missing_evidence") or [],
        }
