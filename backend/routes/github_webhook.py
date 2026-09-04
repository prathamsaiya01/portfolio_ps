from __future__ import annotations

import json
import logging
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request

from backend.config import get_settings
from backend.database import get_database
from backend.services.github_webhook_service import (
    GitHubWebhookService,
    WebhookPayloadError,
    WebhookSignatureError,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/github", tags=["github-webhook"])


@router.post("/webhook")
async def receive_github_webhook(
    request: Request,
    x_github_event: Optional[str] = Header(default=None),
    x_github_delivery: Optional[str] = Header(default=None),
    x_hub_signature_256: Optional[str] = Header(default=None),
):
    raw_body = await request.body()
    try:
        GitHubWebhookService.verify_signature(
            raw_body,
            x_hub_signature_256,
            get_settings().get("github_webhook_secret"),
        )
    except WebhookSignatureError:
        raise HTTPException(status_code=401, detail="Invalid webhook signature") from None

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(status_code=400, detail="Invalid webhook payload") from None
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

    db = get_database()
    if db is None:
        raise HTTPException(status_code=503, detail="Database is not configured")
    if not x_github_event:
        raise HTTPException(status_code=400, detail="Missing GitHub event header")

    try:
        result = await GitHubWebhookService().process(x_github_event, payload, db, x_github_delivery)
    except WebhookPayloadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    except Exception:
        logger.exception("GitHub webhook processing failed")
        raise HTTPException(status_code=500, detail="Webhook processing failed") from None
    return result
