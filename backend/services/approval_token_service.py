from __future__ import annotations

import base64
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet, InvalidToken

from backend.config import get_approval_token_ttl_seconds, get_settings

TOKEN_VERSION = "v1"
ALLOWED_ACTIONS = {"APPROVE", "REJECT", "REVIEW"}


class ApprovalTokenError(ValueError):
    """Raised when an approval token is invalid, expired, or malformed."""


class ApprovalTokenService:
    def __init__(self, secret: Optional[str] = None, ttl_seconds: Optional[int] = None):
        configured_secret = secret or get_settings().get("approval_secret")
        if not configured_secret:
            configured_secret = "development-only-approval-secret"
        key = base64.urlsafe_b64encode(hashlib.sha256(configured_secret.encode("utf-8")).digest())
        self._fernet = Fernet(key)
        self.ttl_seconds = ttl_seconds if ttl_seconds is not None else get_approval_token_ttl_seconds()

    def create_token(self, candidate_id: str, action: str, now: Optional[datetime] = None) -> str:
        normalized_action = str(action).upper()
        if normalized_action not in ALLOWED_ACTIONS:
            raise ApprovalTokenError("Unsupported approval action")
        issued_at = now or datetime.now(timezone.utc)
        payload = {
            "v": TOKEN_VERSION,
            "cid": str(candidate_id),
            "act": normalized_action,
            "iat": int(issued_at.timestamp()),
            "exp": int(issued_at.timestamp()) + self.ttl_seconds,
            "jti": uuid.uuid4().hex,
        }
        return self._fernet.encrypt(json.dumps(payload, separators=(",", ":")).encode("utf-8")).decode("ascii")

    def decode_token(self, token: str, now: Optional[datetime] = None, expected_action: Optional[str] = None) -> Dict[str, Any]:
        try:
            raw_payload = self._fernet.decrypt(token.encode("ascii"), ttl=self.ttl_seconds + 60)
            payload = json.loads(raw_payload.decode("utf-8"))
        except (InvalidToken, ValueError, UnicodeError, json.JSONDecodeError):
            raise ApprovalTokenError("Invalid approval link") from None

        current_time = int((now or datetime.now(timezone.utc)).timestamp())
        if payload.get("v") != TOKEN_VERSION or not payload.get("cid") or not payload.get("jti"):
            raise ApprovalTokenError("Invalid approval link")
        action = str(payload.get("act") or "").upper()
        if action not in ALLOWED_ACTIONS or (expected_action and action != expected_action.upper()):
            raise ApprovalTokenError("This approval link is for a different action")
        if int(payload.get("exp", 0)) <= current_time:
            raise ApprovalTokenError("This approval link has expired")
        return payload
