from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from backend.config import get_settings
from backend.database import get_database
from backend.services.github_service import GitHubService
from backend.services.github_webhook_service import GitHubWebhookService

logger = logging.getLogger(__name__)


class WeeklyAutomationError(RuntimeError):
    pass


class GitHubWeeklyAutomationService:
    STATE_COLLECTION = "github_automation_state"
    RUN_COLLECTION = "github_automation_runs"

    def __init__(self, db: Any = None, github_service: Optional[GitHubService] = None, processor: Optional[GitHubWebhookService] = None):
        self.db = db
        self.github_service = github_service or GitHubService()
        self.processor = processor or GitHubWebhookService(github_service=self.github_service)

    async def run_once(self) -> Dict[str, Any]:
        db = self.db or get_database()
        if db is None:
            raise WeeklyAutomationError("Database is not configured")

        started_at = datetime.now(timezone.utc)
        run_id = f"github-weekly-{uuid.uuid4().hex}"
        summary = {
            "run_id": run_id,
            "started_at": started_at,
            "completed_at": None,
            "status": "RUNNING",
            "repositories_checked": 0,
            "new_repositories_detected": 0,
            "updated_repositories_detected": 0,
            "candidates_created_or_updated": 0,
            "emails_sent": 0,
            "errors": [],
        }
        await db[self.RUN_COLLECTION].insert_one(dict(summary))

        try:
            repositories = await self.github_service.discover_repositories()
        except Exception as exc:
            summary.update({
                "status": "FAILED",
                "completed_at": datetime.now(timezone.utc),
                "errors": [self._safe_error(exc)],
            })
            await db[self.RUN_COLLECTION].update_one({"run_id": run_id}, {"$set": summary})
            return summary

        for repository in repositories:
            summary["repositories_checked"] += 1
            try:
                await self._process_repository(db, repository, summary)
            except Exception as exc:
                error = self._safe_error(exc)
                summary["errors"].append({"repository": repository.get("full_name"), "error": error})
                await self._record_repository_failure(db, repository, error)
                logger.warning("Weekly repository processing failed for %s: %s", repository.get("full_name"), error)

        summary.update({"status": "COMPLETED", "completed_at": datetime.now(timezone.utc)})
        await db[self.RUN_COLLECTION].update_one({"run_id": run_id}, {"$set": summary})
        return summary

    async def _process_repository(self, db: Any, repository: Dict[str, Any], summary: Dict[str, Any]) -> None:
        repo_id = str(repository.get("github_repo_id") or repository.get("id") or "")
        if not repo_id:
            raise WeeklyAutomationError("Repository is missing github_repo_id")

        state_collection = db[self.STATE_COLLECTION]
        state = await state_collection.find_one({"github_repo_id": repo_id})
        pushed_at = repository.get("pushed_at")
        updated_at = repository.get("updated_at")
        current_activity_key = self._activity_key(repo_id, pushed_at or updated_at)
        last_activity_key = (state or {}).get("last_processed_activity_key")
        is_new = state is None
        is_updated = state is not None and current_activity_key != last_activity_key
        if not is_new and not is_updated:
            return

        if is_new:
            summary["new_repositories_detected"] += 1
        else:
            summary["updated_repositories_detected"] += 1

        owner = repository.get("owner") or ""
        name = repository.get("repository_name") or ""
        payload = {
            "repository": {
                "id": int(repo_id),
                "name": name,
                "full_name": repository.get("full_name"),
                "owner": {"login": owner},
            }
        }
        result = await self.processor.process(
            "push",
            payload,
            db,
            delivery_id=f"weekly-{current_activity_key}",
            email_suppressed=False,
            sync_published_metadata=True,
            force_email=(state or {}).get("last_notified_activity_key") != current_activity_key,
            email_activity_key=current_activity_key,
        )
        if result.get("status") != "processed":
            raise WeeklyAutomationError(result.get("reason") or "Repository was not processed")

        email_status = result.get("email_status") or "NOT_SENT"
        if email_status == "FAILED":
            raise WeeklyAutomationError("Email delivery failed")
        if email_status == "SENT":
            summary["emails_sent"] += 1

        if result.get("candidate_id"):
            summary["candidates_created_or_updated"] += 1

        checkpoint = {
            "github_repo_id": repo_id,
            "full_name": repository.get("full_name"),
            "owner": owner,
            "repository_name": name,
            "last_seen_pushed_at": pushed_at,
            "last_seen_updated_at": updated_at,
            "last_processed_activity_key": current_activity_key,
            "last_notified_activity_key": current_activity_key if email_status == "SENT" else (state or {}).get("last_notified_activity_key"),
            "last_successful_check_at": datetime.now(timezone.utc),
            "last_processing_status": "COMPLETED",
            "last_processing_error": None,
            "last_candidate_id": result.get("candidate_id"),
            "last_email_status": email_status,
            "updated_at": datetime.now(timezone.utc),
        }
        await state_collection.update_one({"github_repo_id": repo_id}, {"$set": checkpoint}, upsert=True)

    async def _record_repository_failure(self, db: Any, repository: Dict[str, Any], error: str) -> None:
        repo_id = str(repository.get("github_repo_id") or repository.get("id") or "")
        if not repo_id:
            return
        await db[self.STATE_COLLECTION].update_one(
            {"github_repo_id": repo_id},
            {
                "$set": {
                    "full_name": repository.get("full_name"),
                    "owner": repository.get("owner"),
                    "repository_name": repository.get("repository_name"),
                    "last_processing_status": "FAILED",
                    "last_processing_error": error,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )

    @staticmethod
    def _activity_key(repo_id: str, timestamp: Any) -> str:
        if isinstance(timestamp, datetime):
            value = timestamp.isoformat()
        else:
            value = str(timestamp or "unknown")
        return f"{repo_id}:{value}"

    @staticmethod
    def _safe_error(exc: Exception) -> str:
        message = re.sub(r"(?i)(password|token|secret|authorization|credential)[=:][^\s,;]+", r"\1=[redacted]", str(exc))
        message = re.sub(r"(?i)(mongodb\+srv://|mongodb://)[^\s]+", r"\1[redacted]", message)
        return f"{type(exc).__name__}: {message[:500]}"


def automation_enabled() -> bool:
    value = str(get_settings().get("github_automation_enabled") or "false").lower()
    return value in {"1", "true", "yes", "on"}
