from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query

from backend.database import get_database
from backend.models.candidate import CandidateRecord
from backend.services.email_service import EmailDeliveryError, EmailService

router = APIRouter(prefix="/api/candidates", tags=["candidates"])


@router.post("/{candidate_id}/send-email")
async def send_candidate_email(candidate_id: str):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database is not configured")

    candidate = await db.candidates.find_one({"candidate_id": candidate_id})
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if str(candidate.get("email_status") or "NOT_SENT").upper() == "SENT" and int(candidate.get("email_send_count") or 0) > 0:
        return {"status": "already_sent", "email_status": "SENT"}

    now = datetime.now(timezone.utc)
    try:
        await EmailService().send_candidate_email(candidate)
    except EmailDeliveryError as exc:
        await db.candidates.update_one(
            {"candidate_id": candidate_id},
            {"$set": {"email_status": "FAILED", "updated_at": now}},
        )
        raise HTTPException(status_code=502, detail=str(exc)) from None

    await db.candidates.update_one(
        {"candidate_id": candidate_id},
        {
            "$set": {
                "email_status": "SENT",
                "last_email_sent_at": now,
                "approval_token_issued_at": now,
                "approval_token_version": "v1",
                "updated_at": now,
            },
            "$inc": {"email_send_count": 1},
        },
    )
    return {"status": "sent", "email_status": "SENT", "sent_at": now}


@router.get("")
async def list_candidates(status: str | None = Query(default=None, alias="status")):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database is not configured")

    query: Dict[str, Any] = {}
    if status:
        query["candidate_status"] = status.upper()

    docs = await db.candidates.find(query).sort("created_at", -1).to_list(length=200)
    return [CandidateRecord(**doc).model_dump(mode="python") for doc in docs]


@router.get("/{candidate_id}")
async def get_candidate(candidate_id: str):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database is not configured")

    doc = await db.candidates.find_one({"candidate_id": candidate_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Candidate not found")

    return CandidateRecord(**doc).model_dump(mode="python")


@router.get("/status/{status}")
async def get_candidates_by_status(status: str):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database is not configured")

    docs = await db.candidates.find({"candidate_status": status.upper()}).sort("updated_at", -1).to_list(length=200)
    return [CandidateRecord(**doc).model_dump(mode="python") for doc in docs]
