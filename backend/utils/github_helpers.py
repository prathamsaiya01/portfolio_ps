from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def normalize_repo_payload(repo: Dict[str, Any]) -> Dict[str, Any]:
    languages = repo.get("languages") or []
    if isinstance(languages, dict):
        normalized_languages = list(languages.keys())
    elif isinstance(languages, list):
        normalized_languages = [str(item) for item in languages]
    else:
        normalized_languages = []

    topics = repo.get("topics") or []
    if isinstance(topics, str):
        topics = [topics]

    readme = repo.get("readme") or ""
    created_at = parse_datetime(repo.get("created_at"))
    updated_at = parse_datetime(repo.get("updated_at"))
    last_commit_at = parse_datetime(repo.get("last_commit_at"))

    return {
        "github_repo_id": str(repo.get("id") or repo.get("github_repo_id") or ""),
        "owner": (repo.get("owner") or {}).get("login") if isinstance(repo.get("owner"), dict) else (repo.get("owner") or ""),
        "repository_name": repo.get("name") or "",
        "full_name": repo.get("full_name") or repo.get("fullName") or "",
        "description": repo.get("description") or "",
        "github_url": repo.get("html_url") or repo.get("github_url") or "",
        "homepage_url": repo.get("homepage") or repo.get("homepage_url") or "",
        "readme": readme,
        "languages": normalized_languages,
        "detected_technologies": repo.get("detected_technologies") or [],
        "topics": [str(item) for item in topics],
        "stars": int(repo.get("stargazers_count") or repo.get("stars") or 0),
        "forks": int(repo.get("forks_count") or repo.get("forks") or 0),
        "created_at": created_at,
        "updated_at": updated_at,
        "last_commit_at": last_commit_at,
        "contributors": repo.get("contributors") or [],
        "commit_count": int(repo.get("commit_count") or 0),
        "pull_request_count": int(repo.get("pull_request_count") or 0),
        "issue_count": int(repo.get("issue_count") or 0),
        "repository_visibility": repo.get("visibility") or repo.get("repository_visibility") or "public",
        "portfolio_status": repo.get("portfolio_status") or "DISCOVERED",
        "ai_score": repo.get("ai_score"),
        "ai_analysis": repo.get("ai_analysis") or {},
        "analyzed_at": parse_datetime(repo.get("analyzed_at")),
        "sync_status": repo.get("sync_status") or "synced",
        "last_synced_at": parse_datetime(repo.get("last_synced_at")) or datetime.now(timezone.utc),
    }


def parse_datetime(value: Optional[Any]) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None
