from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from backend.config import get_settings
from backend.database import get_database

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/diagnostics", tags=["diagnostics"])


def _safe_error(exc: Exception) -> str:
    message = str(exc)
    for marker in ("mongodb+srv://", "mongodb://"):
        if marker in message:
            prefix, remainder = message.split(marker, 1)
            message = f"{prefix}{marker}[redacted]@{remainder.split('@')[-1]}"
    return message[:500]


@router.get("/mongodb")
async def mongodb_diagnostic() -> Dict[str, Any]:
    settings = get_settings()
    mongo_url_configured = bool(settings.get("mongo_url"))
    db_name_configured = bool(settings.get("db_name"))
    db = get_database()
    if db is None:
        raise HTTPException(
            status_code=503,
            detail={
                "mongo_url_configured": mongo_url_configured,
                "db_name_configured": db_name_configured,
                "connection_created": False,
                "ping": "failed",
                "published_projects_access": "failed",
                "published_projects_count": None,
                "error_type": "DatabaseNotConfigured",
                "error_message": "MongoDB configuration is incomplete",
            },
        )

    result: Dict[str, Any] = {
        "mongo_url_configured": mongo_url_configured,
        "db_name_configured": db_name_configured,
        "connection_created": True,
        "ping": "failed",
        "published_projects_access": "failed",
        "published_projects_count": None,
        "error_type": "",
        "error_message": "",
    }
    try:
        await db.client.admin.command("ping")
        result["ping"] = "ok"
    except Exception as exc:
        result["error_type"] = type(exc).__name__
        result["error_message"] = _safe_error(exc)
        logger.exception("MongoDB diagnostic ping failed: type=%s", type(exc).__name__)
        return result

    try:
        result["published_projects_count"] = await db.published_projects.count_documents({})
        result["published_projects_access"] = "ok"
    except Exception as exc:
        result["error_type"] = type(exc).__name__
        result["error_message"] = _safe_error(exc)
        logger.exception("MongoDB diagnostic collection query failed: type=%s", type(exc).__name__)
    return result
