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
        return await self.discover_repositories()

    async def discover_repositories(self) -> List[Dict[str, Any]]:
        if not self.username:
            raise GitHubServiceError("GitHub username/owner is not configured.")

        self.discovery_stats = {"listed": 0, "discovered": 0, "skipped": 0, "failed": 0}
        repositories_by_id: Dict[str, Dict[str, Any]] = {}
        list_errors = []
        list_requests = [
            f"{self.base_url}/user/repos?per_page=100&affiliation=owner,collaborator,organization_member",
            f"{self.base_url}/users/{self.username}/repos?per_page=100",
        ]
        for url in list_requests:
            try:
                repositories = await self._request_json(url)
                if not isinstance(repositories, list):
                    continue
                self.discovery_stats["listed"] += len(repositories)
                for repository in repositories:
                    repository_id = str(repository.get("id") or "")
                    if repository_id:
                        repositories_by_id[repository_id] = repository
            except GitHubServiceError as exc:
                list_errors.append(str(exc))
                logger.warning("GitHub repository listing failed for %s: %s", self._safe_url(url), exc)

        if not repositories_by_id and list_errors:
            raise GitHubServiceError("GitHub repository discovery failed") from None

        normalized = []
        for repo in repositories_by_id.values():
            owner = (repo.get("owner") or {}).get("login") if isinstance(repo.get("owner"), dict) else repo.get("owner")
            name = repo.get("name")
            if not owner or not name:
                self.discovery_stats["skipped"] += 1
                continue
            try:
                evidence, contributors = await self._fetch_contribution_evidence(owner, name)
                if not evidence["meaningful_contribution"]:
                    self.discovery_stats["skipped"] += 1
                    logger.info("Skipping repository %s/%s: no meaningful contribution evidence", owner, name)
                    continue
                repo_with_evidence = dict(repo)
                repo_with_evidence["contribution_evidence"] = evidence
                enriched = await self._enrich_repo(repo_with_evidence, contributors=contributors)
                enriched["contribution_evidence"] = evidence
                normalized.append(enriched)
                self.discovery_stats["discovered"] += 1
            except GitHubServiceError as exc:
                self.discovery_stats["failed"] += 1
                logger.warning("GitHub repository processing failed for %s/%s: %s", owner, name, exc)

        return normalized

    async def get_user_contribution_evidence(self, owner: str, repo: str, username: Optional[str] = None) -> Dict[str, Any]:
        evidence, _ = await self._fetch_contribution_evidence(owner, repo, username=username)
        return evidence

    async def _fetch_contribution_evidence(self, owner: str, repo: str, username: Optional[str] = None):
        contributor_username = username or self.username
        repository = await self._request_json(f"{self.base_url}/repos/{owner}/{repo}")
        permissions = repository.get("permissions") if isinstance(repository, dict) else {}
        permissions = permissions if isinstance(permissions, dict) else {}

        commits = await self._request_json(
            f"{self.base_url}/repos/{owner}/{repo}/commits?author={contributor_username}&per_page=100"
        )
        pulls = await self._request_json(f"{self.base_url}/repos/{owner}/{repo}/pulls?state=all&per_page=100")
        contributors = await self._request_json(f"{self.base_url}/repos/{owner}/{repo}/contributors?per_page=100")
        stats_response = await self._request_json(f"{self.base_url}/repos/{owner}/{repo}/stats/contributors", allow_accepted=True)

        commits = commits if isinstance(commits, list) else []
        pulls = pulls if isinstance(pulls, list) else []
        contributors = contributors if isinstance(contributors, list) else []
        stats = stats_response if isinstance(stats_response, list) else []
        contributor_entry = next(
            (
                item for item in contributors
                if str(item.get("login") or (item.get("author") or {}).get("login") or "").lower()
                == str(contributor_username).lower()
            ),
            None,
        )
        authored_pulls = [
            item for item in pulls
            if str((item.get("user") or {}).get("login") or "").lower() == str(contributor_username).lower()
        ]
        contributor_stats = next(
            (item for item in stats if str((item.get("author") or {}).get("login") or "").lower() == str(contributor_username).lower()),
            None,
        )
        stats_commit_count = sum(int(week.get("c") or 0) for week in (contributor_stats or {}).get("weeks", []))
        authored_commit_count = len(commits)
        authored_pull_request_count = len(authored_pulls)
        meaningful = bool(authored_commit_count or authored_pull_request_count or stats_commit_count)
        evidence = {
            "has_repository_access": bool(repository),
            "can_push": bool(permissions.get("push")),
            "authored_commit_count": authored_commit_count,
            "authored_pull_request_count": authored_pull_request_count,
            "contributor_entry_present": contributor_entry is not None,
            "contributor_contribution_count": int((contributor_entry or {}).get("contributions") or 0),
            "contributor_stats_available": contributor_stats is not None,
            "contributor_stats_commit_count": stats_commit_count,
            "meaningful_contribution": meaningful,
        }
        return evidence, contributors

    async def fetch_repository(self, owner: str, repository_name: str) -> Dict[str, Any]:
        if not owner or not repository_name:
            raise GitHubServiceError("GitHub webhook repository is missing owner or name")
        repository = await self._request_json(f"{self.base_url}/repos/{owner}/{repository_name}")
        if not repository:
            raise GitHubServiceError("GitHub repository was not found")
        return await self._enrich_repo(repository)

    async def fetch_repository_by_id(self, github_repo_id: str) -> Dict[str, Any]:
        repository = await self._request_json(f"{self.base_url}/repositories/{github_repo_id}")
        if not repository:
            raise GitHubServiceError("GitHub repository was not found")
        return await self._enrich_repo(repository)

    async def _enrich_repo(self, repo: Dict[str, Any], contributors: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
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

        if contributors is None:
            contributors = await self._request_json(f"{self.base_url}/repos/{owner}/{repo_name}/contributors?per_page=25")
        if isinstance(contributors, list):
            result["contributors"] = [
                item.get("login") or (item.get("author") or {}).get("login")
                for item in contributors
                if item.get("login") or (item.get("author") or {}).get("login")
            ]

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

    async def _request_json(self, url: str, headers: Optional[Dict[str, str]] = None, raw_response: bool = False, allow_accepted: bool = False):
        request_headers = {**self.headers, **(headers or {})}
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(url, headers=request_headers)
                if response.status_code == 202 and allow_accepted:
                    return []
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

    @staticmethod
    def _safe_url(url: str) -> str:
        return url.split("?", 1)[0]
