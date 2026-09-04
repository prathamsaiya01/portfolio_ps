from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from backend.database import get_database
from backend.models.published_project import PublicPublishedProject
from backend.services.portfolio_ranking import PortfolioRankingService

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.get("/projects", response_model=List[PublicPublishedProject])
async def get_published_projects():
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database is not configured")

    try:
        cursor = db.published_projects.find({"status": "PUBLISHED"}).sort("display_order", 1)
        documents = await cursor.to_list(length=500)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Published portfolio is unavailable") from exc

    return [PublicPublishedProject(**document).model_dump(mode="python") for document in documents]


async def _portfolio_documents(db: Any) -> List[Dict[str, Any]]:
    cursor = db.published_projects.find({"status": "PUBLISHED"})
    return await cursor.to_list(length=500)


async def _candidate_documents(db: Any) -> List[Dict[str, Any]]:
    if not hasattr(db, "candidates"):
        return []
    cursor = db.candidates.find({})
    return await cursor.to_list(length=500) if hasattr(cursor, "to_list") else []


@router.get("/ranking")
async def get_portfolio_ranking():
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Portfolio ranking is unavailable")
    try:
        projects = await _portfolio_documents(db)
        candidates = await _candidate_documents(db)
        return PortfolioRankingService().rank_portfolio(projects, candidates)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Portfolio ranking is unavailable") from exc


@router.get("/health")
async def get_portfolio_health():
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Portfolio health is unavailable")
    try:
        projects = await _portfolio_documents(db)
        candidates = await _candidate_documents(db)
        return PortfolioRankingService().portfolio_health(projects, candidates)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Portfolio health is unavailable") from exc

