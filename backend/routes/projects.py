from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from backend.database import get_database
from backend.models.project import ProjectRecord
from backend.portfolio_data import FEATURED_PORTFOLIO
from backend.services.candidate_service import CandidateService
from backend.services.portfolio_intelligence import PortfolioIntelligenceService
from backend.services.project_analyzer import ProjectAnalyzer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("")
async def get_projects(
    portfolio_status: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database is not configured")

    query: Dict[str, Any] = {}
    if portfolio_status:
        query["portfolio_status"] = portfolio_status

    docs = await db.projects.find(query).sort("updated_at_db", -1).limit(limit).to_list(length=limit)
    return [ProjectRecord(**doc).model_dump(mode="python") for doc in docs]


@router.get("/{github_repo_id}")
async def get_project_by_repo_id(github_repo_id: str):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database is not configured")

    doc = await db.projects.find_one({"github_repo_id": github_repo_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")

    return ProjectRecord(**doc).model_dump(mode="python")


@router.get("/status/{portfolio_status}")
async def get_projects_by_status(portfolio_status: str):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database is not configured")

    docs = await db.projects.find({"portfolio_status": portfolio_status}).sort("updated_at_db", -1).to_list(length=500)
    return [ProjectRecord(**doc).model_dump(mode="python") for doc in docs]


@router.post("/{github_repo_id}/analyze")
async def analyze_project(github_repo_id: str):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database is not configured")

    project_doc = await db.projects.find_one({"github_repo_id": github_repo_id})
    if not project_doc:
        raise HTTPException(status_code=404, detail="Project not found")

    project_doc["analysis_status"] = "ANALYZING"
    project_doc["analysis_version"] = "phase2-v1"
    project_doc["analyzed_at"] = datetime.now(timezone.utc)
    await db.projects.update_one({"github_repo_id": github_repo_id}, {"$set": project_doc})

    existing_docs = []
    if hasattr(db.projects, "find"):
        try:
            existing_docs = await db.projects.find({"github_repo_id": {"$ne": github_repo_id}}).to_list(length=100)
        except Exception:
            existing_docs = []
    current = ProjectRecord(**project_doc)

    try:
        analyzer = ProjectAnalyzer()
        analysis = await analyzer.analyze_project(current.model_dump(mode="python"), existing_docs)
    except Exception as exc:
        logger.exception("Project analysis failed")
        await db.projects.update_one(
            {"github_repo_id": github_repo_id},
            {
                "$set": {
                    "analysis_status": "FAILED",
                    "analysis": {},
                    "overall_score": None,
                    "recommendation": "IGNORE",
                    "updated_at_db": datetime.now(timezone.utc),
                }
            },
        )
        raise HTTPException(status_code=503, detail=f"Analysis failed: {exc}") from exc

    payload = {
        "analysis_status": "ANALYZED",
        "analysis_version": "phase2-v1",
        "analyzed_at": datetime.now(timezone.utc),
        "analysis": analysis,
        "overall_score": analysis.get("overall_score"),
        "recommendation": analysis.get("recommendation", "IGNORE"),
        "updated_at_db": datetime.now(timezone.utc),
    }

    await db.projects.update_one({"github_repo_id": github_repo_id}, {"$set": payload})
    return ProjectRecord(**{**project_doc, **payload}).model_dump(mode="python")


@router.get("/{github_repo_id}/analysis")
async def get_project_analysis(github_repo_id: str):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database is not configured")

    doc = await db.projects.find_one({"github_repo_id": github_repo_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")

    if not doc.get("analysis"):
        return {
            "github_repo_id": github_repo_id,
            "analysis_status": doc.get("analysis_status", "NOT_ANALYZED"),
            "analysis": {},
            "overall_score": doc.get("overall_score"),
            "recommendation": doc.get("recommendation", "IGNORE"),
        }
    return {
        "github_repo_id": github_repo_id,
        "analysis_status": doc.get("analysis_status", "NOT_ANALYZED"),
        "analysis": doc.get("analysis") or {},
        "overall_score": doc.get("overall_score"),
        "recommendation": doc.get("recommendation", "IGNORE"),
        "analyzed_at": doc.get("analyzed_at"),
    }


@router.post("/{github_repo_id}/evaluate")
async def evaluate_project_candidate(github_repo_id: str):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database is not configured")

    project_doc = await db.projects.find_one({"github_repo_id": github_repo_id})
    if not project_doc:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project_doc.get("analysis"):
        raise HTTPException(status_code=400, detail="Project analysis is missing. Run the project analysis before evaluation.")

    portfolio_records = list(FEATURED_PORTFOLIO)
    if hasattr(db.projects, "find"):
        try:
            featured_query = db.projects.find({"portfolio_status": "FEATURED"})
            if hasattr(featured_query, "to_list"):
                featured_docs = await featured_query.to_list(length=100)
            elif isinstance(featured_query, list):
                featured_docs = featured_query
            elif hasattr(featured_query, "__await__"):
                featured_docs = await featured_query
            else:
                featured_docs = []
            if featured_docs:
                portfolio_records = featured_docs
        except Exception:
            portfolio_records = list(FEATURED_PORTFOLIO)

    intelligence = PortfolioIntelligenceService(portfolio_records)
    decision = intelligence.evaluate_project(project_doc)
    decision["analysis_version"] = project_doc.get("analysis_version", "phase2-v1")
    decision["recommendation"] = str(project_doc.get("recommendation") or decision.get("candidate_decision", "IGNORE")).upper()

    if decision["candidate_decision"] in {"CANDIDATE", "REVIEW"}:
        candidate_service = CandidateService()
        candidate_existing = await db.candidates.find_one({"github_repo_id": github_repo_id}) if hasattr(db, "candidates") and hasattr(db.candidates, "find_one") else None
        normalized = candidate_service.normalize_decision(project_doc, decision)
        candidate_payload = {
            "candidate_id": candidate_existing.get("candidate_id") if candidate_existing else None,
            "github_repo_id": github_repo_id,
            "project_id": str(project_doc.get("github_repo_id")),
            "repository_name": project_doc.get("repository_name"),
            "full_name": project_doc.get("full_name"),
            "owner": project_doc.get("owner"),
            "description": project_doc.get("description"),
            "github_url": project_doc.get("github_url"),
            "collaborators": project_doc.get("contributors") or [],
            "repository_url": project_doc.get("github_url") or project_doc.get("github_url"),
            "candidate_status": "DISCOVERED" if decision["candidate_decision"] == "REVIEW" else "CANDIDATE",
            "recommendation": decision["candidate_decision"],
            "overall_score": decision["overall_score"],
            "analysis_version": project_doc.get("analysis_version", "phase2-v1"),
            "suggested_title": (project_doc.get("analysis") or {}).get("suggested_title") or project_doc.get("repository_name"),
            "suggested_description": (project_doc.get("analysis") or {}).get("suggested_description") or project_doc.get("description"),
            "strengths": (project_doc.get("analysis") or {}).get("strengths") or [],
            "weaknesses": (project_doc.get("analysis") or {}).get("weaknesses") or [],
            "evidence": (project_doc.get("analysis") or {}).get("evidence") or [],
            "why_it_stands_out": (project_doc.get("analysis") or {}).get("why_it_stands_out") or [],
            "missing_evidence": (project_doc.get("analysis") or {}).get("missing_evidence") or [],
            "candidate_priority": decision.get("candidate_priority"),
            "duplicate_risk": decision.get("duplicate_risk"),
            "portfolio_fit_score": decision.get("portfolio_fit_score"),
            "similarity_flags": decision.get("similarity_flags") or [],
            "differentiation_reason": decision.get("differentiation_reason"),
            "scores": (project_doc.get("analysis") or {}).get("scores") or {},
            "reviewed_at": datetime.now(timezone.utc),
            "rejection_reason": None if decision["candidate_decision"] != "IGNORE" else "Low quality / weak differentiation",
            "created_at": candidate_existing.get("created_at") if candidate_existing else datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        candidate_record = candidate_service.upsert_candidate(candidate_existing, candidate_payload)
        if candidate_existing:
            await db.candidates.update_one({"candidate_id": candidate_existing["candidate_id"]}, {"$set": candidate_record})
        else:
            await db.candidates.insert_one(candidate_record)

    project_doc["portfolio_status"] = "DISCOVERED"
    project_doc["analysis_status"] = "ANALYZED"
    project_doc["analysis_version"] = project_doc.get("analysis_version", "phase2-v1")
    project_doc["recommendation"] = decision["candidate_decision"]
    project_doc["overall_score"] = decision["overall_score"]
    project_doc["updated_at_db"] = datetime.now(timezone.utc)
    await db.projects.update_one({"github_repo_id": github_repo_id}, {"$set": project_doc})

    return {
        "github_repo_id": github_repo_id,
        "candidate_decision": decision["candidate_decision"],
        "overall_score": decision["overall_score"],
        "duplicate_risk": decision["duplicate_risk"],
        "portfolio_fit_score": decision["portfolio_fit_score"],
        "similarity_flags": decision["similarity_flags"],
        "differentiation_reason": decision["differentiation_reason"],
        "candidate_priority": decision["candidate_priority"],
    }
