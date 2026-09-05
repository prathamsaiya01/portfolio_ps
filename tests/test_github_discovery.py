from __future__ import annotations

import asyncio

from backend.services.github_service import GitHubService


class MockGitHubService(GitHubService):
    def __init__(self, responses):
        super().__init__(token="test-token", username="prathamsaiya01")
        self.responses = responses
        self.requested_urls = []

    async def _request_json(self, url, headers=None, raw_response=False, allow_accepted=False):
        self.requested_urls.append(url)
        for matcher, value in sorted(self.responses, key=lambda item: len(item[0]), reverse=True):
            if matcher.startswith("EXACT:") and url == matcher[6:]:
                return value
            if not matcher.startswith("EXACT:") and matcher in url:
                return value
        if url.endswith("/languages"):
            return {"Python": 100}
        if "/topics" in url:
            return {"names": ["automation"]}
        if url.endswith("/readme"):
            return {}
        if "/contributors" in url:
            return []
        if "/stats/contributors" in url:
            return []
        return {}


TARGET = {
    "id": 7001,
    "name": "igniteHackathon404Found",
    "full_name": "Heetshah21/igniteHackathon404Found",
    "owner": {"login": "Heetshah21", "type": "User"},
    "html_url": "https://github.com/Heetshah21/igniteHackathon404Found",
    "permissions": {"admin": False, "maintain": False, "push": True, "triage": True, "pull": True},
    "description": "Collaborator project",
}


def service_for(repositories, commits=None, pulls=None, contributors=None, stats=None):
    return MockGitHubService([
        ("/user/repos?", repositories[0]),
        ("/users/prathamsaiya01/repos", repositories[1]),
        ("EXACT:https://api.github.com/repos/Heetshah21/igniteHackathon404Found", TARGET),
        ("/commits?author=prathamsaiya01", commits or []),
        ("/pulls?state=all", pulls or []),
        ("/contributors?per_page=100", contributors or []),
        ("/stats/contributors", stats or []),
    ])


def test_collaborator_repository_is_discovered_with_commit_evidence():
    service = service_for([[TARGET], []], commits=[{"sha": "hidden"}, {"sha": "hidden"}])

    repositories = asyncio.run(service.discover_repositories())

    assert [item["github_repo_id"] for item in repositories] == ["7001"]
    evidence = repositories[0]["contribution_evidence"]
    assert evidence["has_repository_access"] is True
    assert evidence["can_push"] is True
    assert evidence["authored_commit_count"] == 2
    assert evidence["meaningful_contribution"] is True
    assert any("/user/repos?" in url for url in service.requested_urls)


def test_read_only_collaborator_without_contribution_is_skipped():
    read_only = {**TARGET, "id": 7002, "name": "ReadOnly", "full_name": "Heetshah21/ReadOnly", "permissions": {"pull": True, "push": False}}
    service = MockGitHubService([
        ("/user/repos?", [read_only]),
        ("/users/prathamsaiya01/repos", []),
        ("EXACT:https://api.github.com/repos/Heetshah21/ReadOnly", read_only),
        ("/commits?author=prathamsaiya01", []),
        ("/pulls?state=all", []),
        ("/contributors?per_page=100", [{"login": "someone-else", "contributions": 4}]),
        ("/stats/contributors", []),
    ])

    repositories = asyncio.run(service.discover_repositories())

    assert repositories == []
    assert service.discovery_stats["skipped"] == 1


def test_owner_and_organization_repositories_are_discovered():
    owner = {**TARGET, "id": 7003, "name": "Owned", "full_name": "prathamsaiya01/Owned", "owner": {"login": "prathamsaiya01", "type": "User"}}
    organization = {**TARGET, "id": 7004, "name": "OrgTool", "full_name": "ExampleOrg/OrgTool", "owner": {"login": "ExampleOrg", "type": "Organization"}}
    service = MockGitHubService([
        ("/user/repos?", [organization]),
        ("/users/prathamsaiya01/repos", [owner]),
        ("EXACT:https://api.github.com/repos/ExampleOrg/OrgTool", organization),
        ("EXACT:https://api.github.com/repos/prathamsaiya01/Owned", owner),
        ("/commits?author=prathamsaiya01", [{"sha": "hidden"}]),
        ("/pulls?state=all", []),
        ("/contributors?per_page=100", []),
        ("/stats/contributors", []),
    ])

    repositories = asyncio.run(service.discover_repositories())

    assert {item["full_name"] for item in repositories} == {"ExampleOrg/OrgTool", "prathamsaiya01/Owned"}


def test_duplicate_repository_id_is_returned_once():
    duplicate = {**TARGET, "full_name": "prathamsai01/CopyOfSameId", "owner": {"login": "prathamsaiya01", "type": "User"}}
    service = service_for([[TARGET], [duplicate]], commits=[{"sha": "hidden"}])

    repositories = asyncio.run(service.discover_repositories())

    assert len(repositories) == 1
    assert repositories[0]["github_repo_id"] == "7001"
