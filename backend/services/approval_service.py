from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from backend.services.approval_token_service import ApprovalTokenError, ApprovalTokenService
from backend.services.portfolio_publishing import PortfolioPublishingError, PortfolioPublishingService


class ApprovalService:
    ACTION_TARGETS = {
        "APPROVE": "APPROVED",
        "REJECT": "REJECTED",
        "REVIEW": "REVIEW",
    }
    ELIGIBLE_STATUSES = {"CANDIDATE", "REVIEW"}

    def __init__(self, token_service: ApprovalTokenService | None = None):
        self.token_service = token_service or ApprovalTokenService()

    async def preview(self, db: Any, token: str) -> Dict[str, Any]:
        payload = self.token_service.decode_token(token)
        candidate = await db.candidates.find_one({"candidate_id": payload["cid"]})
        if not candidate:
            raise ApprovalTokenError("Invalid approval link")
        return {
            "action": payload["act"],
            "candidate_name": candidate.get("suggested_title") or candidate.get("repository_name") or "This project",
            "expires_at": datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        }

    async def apply(self, db: Any, token: str, expected_action: str | None = None) -> Dict[str, Any]:
        payload = self.token_service.decode_token(token, expected_action=expected_action)
        candidate = await db.candidates.find_one({"candidate_id": payload["cid"]})
        if not candidate:
            raise ApprovalTokenError("Invalid approval link")

        consumed_tokens = list(candidate.get("consumed_approval_token_ids") or [])
        if payload["jti"] in consumed_tokens:
            return self._result(candidate, "already_processed")

        current_status = str(candidate.get("candidate_status") or "").upper()
        action = payload["act"]
        target_status = self.ACTION_TARGETS[action]
        if current_status not in self.ELIGIBLE_STATUSES:
            return self._result(candidate, "already_processed")

        now = datetime.now(timezone.utc)
        consumed_tokens.append(payload["jti"])
        update = {
            "candidate_status": target_status,
            "status": target_status,
            "recommendation": target_status,
            "decision": target_status,
            "decision_at": now,
            "decision_source": "EMAIL",
            "approval_token_version": payload["v"],
            "consumed_approval_token_ids": consumed_tokens,
            "updated_at": now,
            "reviewed_at": now,
            "approval_status": target_status,
        }
        if action == "REJECT":
            update["rejection_reason"] = "Rejected through email approval workflow"
        if action == "REVIEW":
            update["review_reason"] = "Marked for later review through email approval workflow"
        await db.candidates.update_one({"candidate_id": payload["cid"]}, {"$set": update})
        updated_candidate = {**candidate, **update}
        if action == "APPROVE":
            try:
                published = await PortfolioPublishingService().publish_approved_candidate(db, updated_candidate)
            except PortfolioPublishingError as exc:
                # Approval is authoritative; publication can be retried without changing it.
                if str(exc) not in {"Published portfolio is not configured", "Approved candidate has no repository identity"}:
                    await db.candidates.update_one(
                        {"candidate_id": payload["cid"]},
                        {"$set": {"publishing_status": "FAILED", "publishing_error": "Publishing failed", "updated_at": datetime.now(timezone.utc)}},
                    )
                    updated_candidate.update({"publishing_status": "FAILED", "publishing_error": "Publishing failed"})
            except Exception:
                await db.candidates.update_one(
                    {"candidate_id": payload["cid"]},
                    {"$set": {"publishing_status": "FAILED", "publishing_error": "Publishing failed", "updated_at": datetime.now(timezone.utc)}},
                )
                updated_candidate.update({"publishing_status": "FAILED", "publishing_error": "Publishing failed"})
            else:
                await db.candidates.update_one(
                    {"candidate_id": payload["cid"]},
                    {"$set": {"publishing_status": "PUBLISHED", "publishing_error": None, "published_project_id": published.get("id"), "updated_at": datetime.now(timezone.utc)}},
                )
                updated_candidate.update({"publishing_status": "PUBLISHED", "published_project_id": published.get("id")})
        return self._result(updated_candidate, "processed")

    @staticmethod
    def _result(candidate: Dict[str, Any], status: str) -> Dict[str, Any]:
        return {
            "status": status,
            "decision": candidate.get("decision") or candidate.get("candidate_status"),
            "candidate_name": candidate.get("suggested_title") or candidate.get("repository_name") or "This project",
        }
