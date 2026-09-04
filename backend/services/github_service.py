from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx

from backend.config import get_settings
from backend.utils.github_helpers import normalize_repo_payload

logger = logging.getLogger(__name__)


class GitHubServiceError(RuntimeError):
    pass


class GitHubService:
    def __init__(self, token: Optional[str] = None, username: Optional[str] = None):
        settings = get_settings()
        self.token = token or settings.get("github_token")
        self.username = username or settings.get("github_username")
        self.base_url = settings.get("github_api_base_url", "https://api.github.com")
        self.headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "portfolio-automator",
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    async def fetch_repositories(self) -> List[Dict[str, Any]]:
        if not self.username:
            raise GitHubServiceError("GitHub username/owner is not configured.")

        url = f"{self.base_url}/users/{self.username}/repos?per_page=100"
        repositories = await self._request_json(url)
        normalized = []

        for repo in repositories:
            normalized.append(await self._enrich_repo(repo))

        return normalized

    async def fetch_repository(self, owner: str, repository_name: str) -> Dict[str, Any]:
        if not owner or not repository_name:
            raise GitHubServiceError("GitHub webhook repository is missing owner or name")
        repository = await self._request_json(f"{self.base_url}/repos/{owner}/{repository_name}")
        if not repository:
            raise GitHubServiceError("GitHub repository was not found")
        return await self._enrich_repo(repository)

    async def _enrich_repo(self, repo: Dict[str, Any]) -> Dict[str, Any]:
        repo_id = repo.get("id")
        if repo_id is None:
            raise GitHubServiceError("GitHub repository missing id field")

        repo_name = repo.get("name")
        owner = repo.get("owner", {}).get("login") if isinstance(repo.get("owner"), dict) else self.username

        result = dict(repo)
        result["owner"] = {"login": owner}
        result["full_name"] = repo.get("full_name") or f"{owner}/{repo_name}"

        languages = await self._request_json(f"{self.base_url}/repos/{owner}/{repo_name}/languages")
        if isinstance(languages, dict):
            result["languages"] = languages

        topics = await self._request_json(f"{self.base_url}/repos/{owner}/{repo_name}/topics", headers={"Accept": "application/vnd.github+json"})
        if isinstance(topics, dict):
            result["topics"] = topics.get("names", [])

        readme = await self._fetch_readme(owner, repo_name)
        if readme:
            result["readme"] = readme

        contributors = await self._request_json(f"{self.base_url}/repos/{owner}/{repo_name}/contributors?per_page=25")
        if isinstance(contributors, list):
            result["contributors"] = [item.get("login") for item in contributors if item.get("login")]

        return normalize_repo_payload(result)

    async def _fetch_readme(self, owner: str, repo_name: str) -> str:
        try:
            response = await self._request_json(f"{self.base_url}/repos/{owner}/{repo_name}/readme", raw_response=True)
            if response is None:
                return ""
            content = response.get("content") or ""
            import base64
            try:
                return base64.b64decode(content).decode("utf-8", errors="replace")
            except Exception:
                return content
        except Exception:
            return ""

    async def _request_json(self, url: str, headers: Optional[Dict[str, str]] = None, raw_response: bool = False):
        request_headers = {**self.headers, **(headers or {})}
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(url, headers=request_headers)
                if response.status_code == 404:
                    return {} if raw_response else []
                if response.status_code >= 400:
                    raise GitHubServiceError(
                        f"GitHub API request failed with status {response.status_code} for {url}"
                    )
                payload = response.json()
                if raw_response:
                    return payload
                return payload
        except Exception as exc:
            logger.exception("GitHub API request error")
            if isinstance(exc, httpx.HTTPError):
                raise GitHubServiceError(f"Unable to reach GitHub API: {exc}") from exc
            raise GitHubServiceError(f"GitHub API request failed: {exc}") from exc
