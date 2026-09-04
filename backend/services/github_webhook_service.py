from __future__ import annotations

import hashlib
import hmac
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.portfolio_data import FEATURED_PORTFOLIO
from backend.services.candidate_service import CandidateService
from backend.services.email_service import EmailDeliveryError, EmailService
from backend.services.github_service import GitHubService
from backend.services.portfolio_intelligence import PortfolioIntelligenceService
from backend.services.project_analyzer import ProjectAnalyzer
from backend.services.portfolio_publishing import PortfolioPublishingService
from backend.utils.github_helpers import normalize_repo_payload

logger = logging.getLogger(__name__)

SUPPORTED_EVENTS = {
    "push": None,
    "pull_request": {"opened", "reopened", "synchronize", "closed"},
    "release": {"created", "edited", "published"},
    "repository": {"created", "edited", "renamed", "transferred"},
}
TERMINAL_CANDIDATE_STATUSES = {"APPROVED", "REJECTED"}


class WebhookSignatureError(ValueError):
    pass


class WebhookPayloadError(ValueError):
    pass


class GitHubWebhookService:
    def __init__(
        self,
        github_service: Optional[GitHubService] = None,
        analyzer: Optional[ProjectAnalyzer] = None,
        email_service: Optional[EmailService] = None,
    ):
        self.github_service = github_service or GitHubService()
        self.analyzer = analyzer or ProjectAnalyzer()
        self.email_service = email_service or EmailService()

    @staticmethod
    def verify_signature(raw_body: bytes, signature: Optional[str], secret: Optional[str]) -> None:
        if not secret or not signature or not signature.startswith("sha256="):
            raise WebhookSignatureError("Invalid webhook signature")
        expected = "sha256=" + hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise WebhookSignatureError("Invalid webhook signature")

    @staticmethod
    def is_relevant_event(event: str, payload: Dict[str, Any]) -> bool:
        event_name = (event or "").lower()
        if event_name not in SUPPORTED_EVENTS:
            return False
        allowed_actions = SUPPORTED_EVENTS[event_name]
        return allowed_actions is None or str(payload.get("action") or "").lower() in allowed_actions

    async def process(self, event: str, payload: Dict[str, Any], db: Any, delivery_id: Optional[str] = None) -> Dict[str, Any]:
        if not self.is_relevant_event(event, payload):
            return {"status": "ignored", "event": event, "reason": "event is not relevant"}

        repository = payload.get("repository") or {}
        owner_data = repository.get("owner") or {}
        owner = owner_data.get("login") if isinstance(owner_data, dict) else owner_data
        name = repository.get("name")
        if not owner or not name:
            raise WebhookPayloadError("Webhook repository information is incomplete")

        repository_id = str(repository.get("id") or "")
        existing_project = await db.projects.find_one({"github_repo_id": repository_id}) if repository_id else None
        if delivery_id and existing_project and existing_project.get("last_webhook_delivery_id") == delivery_id:
            return {"status": "duplicate", "event": event, "github_repo_id": repository_id}

        fetched = await self.github_service.fetch_repository(str(owner), str(name))
        normalized = normalize_repo_payload(fetched)
        now = datetime.now(timezone.utc)
        project_doc = {**(existing_project or {}), **normalized}
        project_doc.update({
            "analysis_status": "ANALYZING",
            "analysis_version": "phase2-v1",
            "last_webhook_event": event,
            "last_webhook_delivery_id": delivery_id,
            "last_synced_at": now,
            "updated_at_db": now,
        })
        if existing_project:
            await db.projects.update_one({"github_repo_id": normalized["github_repo_id"]}, {"$set": project_doc})
        else:
            project_doc["created_at_db"] = now
            await db.projects.insert_one(project_doc)

        existing_projects = await self._load_projects(db, normalized["github_repo_id"])
        analysis = await self.analyzer.analyze_project(project_doc, existing_projects)
        project_doc.update({
            "analysis_status": "ANALYZED",
            "analysis": analysis,
            "overall_score": analysis.get("overall_score"),
            "recommendation": analysis.get("recommendation", "IGNORE"),
            "analyzed_at": now,
            "updated_at_db": now,
        })
        await db.projects.update_one({"github_repo_id": normalized["github_repo_id"]}, {"$set": project_doc})
        await PortfolioPublishingService().sync_project_metadata(db, project_doc)

        portfolio_records = await self._load_featured(db)
        decision = PortfolioIntelligenceService(portfolio_records).evaluate_project(project_doc)
        candidate = None
        email_status = "NOT_SENT"
        if decision["candidate_decision"] in {"CANDIDATE", "REVIEW"}:
            candidate = await self._upsert_candidate(db, project_doc, decision)
            if decision["candidate_decision"] == "CANDIDATE" and candidate.get("candidate_status") not in TERMINAL_CANDIDATE_STATUSES:
                if str(candidate.get("email_status") or "NOT_SENT").upper() != "SENT":
                    try:
                        await self.email_service.send_candidate_email(candidate)
                    except EmailDeliveryError:
                        email_status = "FAILED"
                        await db.candidates.update_one(
                            {"candidate_id": candidate["candidate_id"]},
                            {"$set": {"email_status": "FAILED", "updated_at": datetime.now(timezone.utc)}},
                        )
                    else:
                        email_status = "SENT"
                        await db.candidates.update_one(
                            {"candidate_id": candidate["candidate_id"]},
                            {
                                "$set": {
                                    "email_status": "SENT",
                                    "last_email_sent_at": datetime.now(timezone.utc),
                                    "approval_token_issued_at": datetime.now(timezone.utc),
                                    "approval_token_version": "v1",
                                    "updated_at": datetime.now(timezone.utc),
                                },
                                "$inc": {"email_send_count": 1},
                            },
                        )
                else:
                    email_status = "SENT"

        return {
            "status": "processed",
            "event": event,
            "github_repo_id": normalized["github_repo_id"],
            "analysis_status": project_doc["analysis_status"],
            "candidate_decision": decision["candidate_decision"],
            "candidate_id": candidate.get("candidate_id") if candidate else None,
            "email_status": email_status,
        }

    async def _load_projects(self, db: Any, repository_id: str) -> List[Dict[str, Any]]:
        if not hasattr(db.projects, "find"):
            return []
        try:
            query = db.projects.find({"github_repo_id": {"$ne": repository_id}})
            return await query.to_list(length=100) if hasattr(query, "to_list") else []
        except Exception:
            return []

    async def _load_featured(self, db: Any) -> List[Dict[str, Any]]:
        try:
            query = db.projects.find({"portfolio_status": "FEATURED"})
            records = await query.to_list(length=100) if hasattr(query, "to_list") else []
            return records or list(FEATURED_PORTFOLIO)
        except Exception:
            return list(FEATURED_PORTFOLIO)

    async def _upsert_candidate(self, db: Any, project: Dict[str, Any], decision: Dict[str, Any]) -> Dict[str, Any]:
        candidate_existing = await db.candidates.find_one({"github_repo_id": project["github_repo_id"]})
        candidate_service = CandidateService()
        current_status = str((candidate_existing or {}).get("candidate_status") or "").upper()
        payload = {
            "candidate_id": (candidate_existing or {}).get("candidate_id"),
            "github_repo_id": project["github_repo_id"],
            "project_id": project["github_repo_id"],
            "repository_name": project.get("repository_name"),
            "full_name": project.get("full_name"),
            "owner": project.get("owner"),
            "description": project.get("description"),
            "github_url": project.get("github_url"),
            "collaborators": project.get("contributors") or [],
            "candidate_status": current_status if current_status in TERMINAL_CANDIDATE_STATUSES else "CANDIDATE",
            "recommendation": current_status if current_status in TERMINAL_CANDIDATE_STATUSES else decision["candidate_decision"],
            "overall_score": decision["overall_score"],
            "analysis_version": project.get("analysis_version", "phase2-v1"),
            "suggested_title": (project.get("analysis") or {}).get("suggested_title") or project.get("repository_name"),
            "suggested_description": (project.get("analysis") or {}).get("suggested_description") or project.get("description"),
            "strengths": (project.get("analysis") or {}).get("strengths") or [],
            "weaknesses": (project.get("analysis") or {}).get("weaknesses") or [],
            "evidence": (project.get("analysis") or {}).get("evidence") or [],
            "why_it_stands_out": (project.get("analysis") or {}).get("why_it_stands_out") or [],
            "missing_evidence": (project.get("analysis") or {}).get("missing_evidence") or [],
            "candidate_priority": decision.get("candidate_priority"),
            "duplicate_risk": decision.get("duplicate_risk"),
            "portfolio_fit_score": decision.get("portfolio_fit_score"),
            "similarity_flags": decision.get("similarity_flags") or [],
            "differentiation_reason": decision.get("differentiation_reason"),
            "scores": (project.get("analysis") or {}).get("scores") or {},
            "created_at": (candidate_existing or {}).get("created_at") or datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        record = candidate_service.upsert_candidate(candidate_existing, payload)
        if candidate_existing:
            await db.candidates.update_one({"candidate_id": candidate_existing["candidate_id"]}, {"$set": record})
        else:
            await db.candidates.insert_one(record)
        return record
