from __future__ import annotations

import hmac
from typing import Any, Dict

from fastapi import APIRouter, Header, HTTPException, Query

from backend.config import get_settings
from backend.database import get_database
from backend.services.github_service import GitHubService, GitHubServiceError
from backend.services.github_webhook_service import GitHubWebhookService, WebhookPayloadError

router = APIRouter(prefix="/api/admin", tags=["admin-processing"])


@router.post("/process-repository/{github_repo_id}")
async def process_single_repository(
    github_repo_id: str,
    email_suppressed: bool = Query(default=False),
    x_admin_secret: str | None = Header(default=None),
) -> Dict[str, Any]:
    settings = get_settings()
    configured_secret = settings.get("admin_secret") or settings.get("approval_secret")
    if not configured_secret or not x_admin_secret or not hmac.compare_digest(x_admin_secret, configured_secret):
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    if not github_repo_id.isdigit():
        raise HTTPException(status_code=400, detail="github_repo_id must be numeric")
    if not email_suppressed:
        raise HTTPException(status_code=400, detail="email_suppressed=true is required")

    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database is not configured")

    try:
        repository = await GitHubService().fetch_repository_by_id(github_repo_id)
        owner = repository.get("owner") or ""
        name = repository.get("repository_name") or ""
        payload = {
            "repository": {
                "id": int(github_repo_id),
                "name": name,
                "full_name": repository.get("full_name"),
                "owner": {"login": owner},
            }
        }
        result = await GitHubWebhookService().process(
            "push",
            payload,
            db,
            delivery_id=f"admin-test-{github_repo_id}",
            email_suppressed=True,
            sync_published_metadata=False,
        )
    except (GitHubServiceError, WebhookPayloadError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from None

    project = await db.projects.find_one({"github_repo_id": github_repo_id})
    candidate = await db.candidates.find_one({"github_repo_id": github_repo_id})
    return {
        "github_repo_id": github_repo_id,
        "full_name": repository.get("full_name"),
        "project_id": project.get("github_repo_id") if project else None,
        "candidate_id": candidate.get("candidate_id") if candidate else result.get("candidate_id"),
        "overall_score": project.get("overall_score") if project else None,
        "recommendation": result.get("candidate_decision"),
        "ai_analysis_status": project.get("analysis_status") if project else None,
        "candidate_status": candidate.get("candidate_status") if candidate else None,
        "email_sent": False,
        "published": False,
    }