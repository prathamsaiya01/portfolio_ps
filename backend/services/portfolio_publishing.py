from __future__ import annotations

import uuid
import inspect
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class PortfolioPublishingError(RuntimeError):
    """Raised when a published-project operation cannot complete."""


class PortfolioPublishingService:
    PUBLISHED = "PUBLISHED"
    UNPUBLISHED = "UNPUBLISHED"

    async def publish_approved_candidate(self, db: Any, candidate: Dict[str, Any], project: Optional[Dict[str, Any]] = None, project_name: Optional[str] = None) -> Dict[str, Any]:
        if str(candidate.get("candidate_status") or "").upper() != "APPROVED":
            raise PortfolioPublishingError("Only approved candidates can be published")
        project_name = project_name.strip() if project_name else None
        collection = getattr(db, "published_projects", None)
        if collection is None or not hasattr(collection, "find_one"):
            raise PortfolioPublishingError("Published portfolio is not configured")

        project_collection = getattr(db, "projects", None)
        if not project and project_collection is not None and hasattr(project_collection, "find_one"):
            project_result = project_collection.find_one({"github_repo_id": candidate.get("github_repo_id")})
            project = await project_result if inspect.isawaitable(project_result) else {}
        project = project or {}
        repo_id = str(candidate.get("github_repo_id") or project.get("github_repo_id") or "")
        if not repo_id:
            raise PortfolioPublishingError("Approved candidate has no repository identity")

        now = datetime.now(timezone.utc)
        existing_result = collection.find_one({"github_repo_id": repo_id})
        if not inspect.isawaitable(existing_result):
            raise PortfolioPublishingError("Published portfolio is not configured")
        existing = await existing_result
        if existing:
            record = self._updated_record(existing, candidate, project, now, project_name)
            await collection.update_one({"github_repo_id": repo_id}, {"$set": record})
            return record

        display_order = await self._next_display_order(collection)
        record = self._new_record(candidate, project, now, display_order, project_name)
        await collection.insert_one(record)
        return record

    async def unpublish_project(self, db: Any, github_repo_id: str) -> Dict[str, Any]:
        collection = getattr(db, "published_projects", None)
        if collection is None:
            raise PortfolioPublishingError("Published portfolio is not configured")
        existing_result = collection.find_one({"github_repo_id": str(github_repo_id)})
        if not inspect.isawaitable(existing_result):
            raise PortfolioPublishingError("Published portfolio is not configured")
        existing = await existing_result
        if not existing:
            raise PortfolioPublishingError("Published project not found")
        update = {"status": self.UNPUBLISHED, "updated_at": datetime.now(timezone.utc)}
        await collection.update_one({"github_repo_id": str(github_repo_id)}, {"$set": update})
        return {**existing, **update}

    async def sync_project_metadata(self, db: Any, project: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        repo_id = str(project.get("github_repo_id") or "")
        collection = getattr(db, "published_projects", None)
        if not repo_id or collection is None:
            return None
        existing_result = collection.find_one({"github_repo_id": repo_id})
        if not inspect.isawaitable(existing_result):
            return None
        existing = await existing_result
        if not existing or str(existing.get("status") or self.PUBLISHED).upper() != self.PUBLISHED:
            return None
        update = {
            "github_url": project.get("github_url") or existing.get("github_url"),
            "languages": project.get("languages") or existing.get("languages") or [],
            "technologies": project.get("detected_technologies") or existing.get("technologies") or [],
            "topics": project.get("topics") or existing.get("topics") or [],
            "live_url": existing.get("live_url") if existing.get("live_url_manual") else project.get("homepage_url") or existing.get("live_url"),
            "description": existing.get("description") if existing.get("description_manual") else project.get("description") or existing.get("description", ""),
            "updated_at": datetime.now(timezone.utc),
        }
        await collection.update_one({"github_repo_id": repo_id}, {"$set": update})
        return {**existing, **update}

    async def _next_display_order(self, collection: Any) -> int:
        try:
            cursor = collection.find({"status": self.PUBLISHED})
            records = await cursor.to_list(length=1000) if hasattr(cursor, "to_list") else []
            return max((int(record.get("display_order") or 0) for record in records), default=0) + 1
        except Exception:
            return 1

    @staticmethod
    def _new_record(candidate: Dict[str, Any], project: Dict[str, Any], now: datetime, display_order: int, project_name: Optional[str] = None) -> Dict[str, Any]:
        return {
            "id": f"published-{uuid.uuid4().hex}",
            "github_repo_id": str(candidate.get("github_repo_id") or project.get("github_repo_id")),
            "candidate_id": candidate.get("candidate_id"),
            "title": project_name or candidate.get("suggested_title") or candidate.get("repository_name") or project.get("repository_name") or "Untitled project",
            "description": candidate.get("suggested_description") or candidate.get("description") or project.get("description") or "",
            "github_url": candidate.get("github_url") or project.get("github_url"),
            "live_url": candidate.get("live_url") or project.get("homepage_url"),
            "image_url": candidate.get("image_url") or project.get("image_url"),
            "languages": candidate.get("languages") or project.get("languages") or [],
            "technologies": candidate.get("technologies") or project.get("detected_technologies") or [],
            "topics": candidate.get("topics") or project.get("topics") or [],
            "category": candidate.get("category") or "Software Project",
            "featured": bool(candidate.get("featured", False)),
            "display_order": display_order,
            "status": PortfolioPublishingService.PUBLISHED,
            "published_at": now,
            "updated_at": now,
            "source": "GITHUB_APPROVAL",
            "created_at": now,
            "title_manual": False,
            "description_manual": False,
            "live_url_manual": False,
        }

    @staticmethod
    def _updated_record(existing: Dict[str, Any], candidate: Dict[str, Any], project: Dict[str, Any], now: datetime, project_name: Optional[str] = None) -> Dict[str, Any]:
        updated = dict(existing)
        updated.update({
            "candidate_id": existing.get("candidate_id") or candidate.get("candidate_id"),
            "github_url": candidate.get("github_url") or project.get("github_url") or existing.get("github_url"),
            "languages": project.get("languages") or candidate.get("languages") or existing.get("languages") or [],
            "technologies": project.get("detected_technologies") or candidate.get("technologies") or existing.get("technologies") or [],
            "topics": project.get("topics") or candidate.get("topics") or existing.get("topics") or [],
            "live_url": existing.get("live_url") if existing.get("live_url_manual") else candidate.get("live_url") or project.get("homepage_url") or existing.get("live_url"),
            "description": existing.get("description") if existing.get("description_manual") else candidate.get("suggested_description") or candidate.get("description") or project.get("description") or existing.get("description", ""),
            "status": PortfolioPublishingService.PUBLISHED,
            "updated_at": now,
        })
        if project_name:
            updated["title"] = project_name
        elif not existing.get("title_manual"):
            updated["title"] = candidate.get("suggested_title") or candidate.get("repository_name") or project.get("repository_name") or existing.get("title")
        return updated
