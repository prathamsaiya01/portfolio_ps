from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.database import get_database
from backend.services.github_service import GitHubService, GitHubServiceError
from backend.utils.github_helpers import normalize_repo_payload

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/github", tags=["github"])


class GitHubSyncResponse(BaseModel):
    status: str
    repositories_fetched: int
    repositories_upserted: int
    repositories_skipped: int
    owner: str
    synced_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


@router.post("/sync", response_model=GitHubSyncResponse)
async def sync_github_repositories():
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database is not configured")

    service = GitHubService()
    try:
        repositories = await service.discover_repositories()
    except GitHubServiceError as exc:  # pragma: no cover - exercised in tests via mocks
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if not isinstance(repositories, list):
        raise HTTPException(status_code=502, detail="GitHub API returned an unexpected response")

    inserted = 0
    skipped = 0
    owner = service.username or "unknown"
    seen_repo_ids = set()

    for repo in repositories:
        normalized = normalize_repo_payload(repo)
        github_repo_id = normalized.get("github_repo_id")
        if not github_repo_id:
            skipped += 1
            continue
        if github_repo_id in seen_repo_ids:
            skipped += 1
            continue
        seen_repo_ids.add(github_repo_id)

        existing = await db.projects.find_one({"github_repo_id": github_repo_id})
        if existing:
            normalized["updated_at_db"] = datetime.now(timezone.utc)
            normalized["last_synced_at"] = datetime.now(timezone.utc)
            await db.projects.update_one({"github_repo_id": github_repo_id}, {"$set": normalized})
            inserted += 1
            continue

        normalized["created_at_db"] = datetime.now(timezone.utc)
        normalized["updated_at_db"] = datetime.now(timezone.utc)
        normalized["last_synced_at"] = datetime.now(timezone.utc)
        await db.projects.insert_one(normalized)
        inserted += 1

    return GitHubSyncResponse(
        status="success",
        repositories_fetched=service.discovery_stats.get("listed", len(repositories)),
        repositories_upserted=inserted,
        repositories_skipped=skipped + service.discovery_stats.get("skipped", 0) + service.discovery_stats.get("failed", 0),
        owner=owner,
    )
