from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.database import get_database
from backend.services.approval_service import ApprovalService
from backend.services.approval_token_service import ApprovalTokenError

router = APIRouter(prefix="/api/approval", tags=["approval"])


class ApprovalActionRequest(BaseModel):
    action: Optional[str] = None


def _approval_error(exc: ApprovalTokenError) -> HTTPException:
    detail = str(exc)
    if detail == "This approval link has expired":
        return HTTPException(status_code=410, detail="This approval link has expired")
    return HTTPException(status_code=400, detail=detail if detail in {"This approval link is for a different action"} else "This approval link is invalid")


@router.get("/{token}")
async def preview_approval(token: str):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Approval service is unavailable")
    try:
        return await ApprovalService().preview(db, token)
    except ApprovalTokenError as exc:
        raise _approval_error(exc) from None


@router.post("/{token}")
async def apply_approval(token: str, request: ApprovalActionRequest | None = None):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Approval service is unavailable")
    try:
        expected_action = request.action.upper() if request and request.action else None
        result = await ApprovalService().apply(db, token, expected_action=expected_action)
        return result
    except ApprovalTokenError as exc:
        raise _approval_error(exc) from None
