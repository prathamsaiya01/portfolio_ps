from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.services.github_weekly_automation import GitHubWeeklyAutomationService


class Cursor:
    def __init__(self, records):
        self.records = list(records)

    async def to_list(self, length=1000):
        return self.records[:length]


class Collection:
    def __init__(self):
        self.records = []

    async def find_one(self, query):
        for item in self.records:
            if all(item.get(key) == value for key, value in query.items()):
                return dict(item)
        return None

    async def insert_one(self, document):
        self.records.append(dict(document))

    async def update_one(self, query, update, upsert=False):
        existing = await self.find_one(query)
        if existing is None:
            if upsert:
                self.records.append(dict(update.get("$set", {})))
            return
        for item in self.records:
            if all(item.get(key) == value for key, value in query.items()):
                item.update(update.get("$set", {}))
                return

    def find(self, query):
        return Cursor([item for item in self.records if all(item.get(key) == value for key, value in query.items())])


class Db:
    def __init__(self):
        self.github_automation_state = Collection()
        self.github_automation_runs = Collection()

    def __getitem__(self, name):
        return getattr(self, name)


def repo(repo_id="1", pushed_at="2026-09-01T00:00:00+00:00"):
    return {
        "github_repo_id": repo_id,
        "full_name": f"owner/repo-{repo_id}",
        "owner": "owner",
        "repository_name": f"repo-{repo_id}",
        "pushed_at": datetime.fromisoformat(pushed_at) if pushed_at else None,
        "updated_at": datetime.fromisoformat(pushed_at) if pushed_at else None,
    }


def processor_result(repo_id, decision="CANDIDATE", email_status="SENT", candidate_id="candidate-1"):
    return {
        "status": "processed",
        "github_repo_id": repo_id,
        "candidate_decision": decision,
        "candidate_id": candidate_id if decision in {"CANDIDATE", "REVIEW"} else None,
        "email_status": email_status,
    }


def make_service(db, repositories, results=None, errors=None):
    github = MagicMock()
    github.discover_repositories = AsyncMock(return_value=repositories)
    processor = MagicMock()
    results = results or {}
    errors = errors or {}

    async def process(*args, **kwargs):
        repository_id = str(args[1]["repository"]["id"])
        if repository_id in errors:
            raise errors[repository_id]
        return results.get(repository_id, processor_result(repository_id))

    processor.process = AsyncMock(side_effect=process)
    return GitHubWeeklyAutomationService(db=db, github_service=github, processor=processor), github, processor


def test_new_repository_is_processed_and_checkpointed():
    db = Db()
    service, github, processor = make_service(db, [repo("1")])
    summary = asyncio.run(service.run_once())
    assert summary["new_repositories_detected"] == 1
    processor.process.assert_awaited_once()
    assert db.github_automation_state.records[0]["github_repo_id"] == "1"
    assert db.github_automation_state.records[0]["last_notified_activity_key"].startswith("1:")


def test_new_repository_with_meaningful_contribution_is_processed():
    db = Db()
    repository = {**repo("1"), "contribution_evidence": {"meaningful_contribution": True, "authored_commit_count": 2}}
    service, _, processor = make_service(db, [repository])
    asyncio.run(service.run_once())
    assert processor.process.await_count == 1


def test_access_only_repository_is_not_processed_when_discovery_filters_it():
    db = Db()
    service, github, processor = make_service(db, [])
    summary = asyncio.run(service.run_once())
    assert summary["repositories_checked"] == 0
    processor.process.assert_not_awaited()


def test_existing_repository_without_new_push_is_ignored():
    db = Db()
    db.github_automation_state.records.append({"github_repo_id": "1", "last_processed_activity_key": "1:2026-09-01T00:00:00+00:00"})
    service, _, processor = make_service(db, [repo("1")])
    summary = asyncio.run(service.run_once())
    assert summary["updated_repositories_detected"] == 0
    processor.process.assert_not_awaited()


def test_existing_repository_with_new_push_is_processed_and_can_email_again():
    db = Db()
    db.github_automation_state.records.append({"github_repo_id": "1", "last_processed_activity_key": "1:2026-09-01T00:00:00+00:00", "last_notified_activity_key": "1:2026-09-01T00:00:00+00:00"})
    service, _, processor = make_service(db, [repo("1", "2026-09-08T00:00:00+00:00")])
    summary = asyncio.run(service.run_once())
    assert summary["updated_repositories_detected"] == 1
    assert summary["emails_sent"] == 1
    processor.process.assert_awaited_once()


def test_same_activity_does_not_send_duplicate_email():
    db = Db()
    key = "1:2026-09-01T00:00:00+00:00"
    db.github_automation_state.records.append({"github_repo_id": "1", "last_processed_activity_key": key, "last_notified_activity_key": key})
    service, _, processor = make_service(db, [repo("1")])
    summary = asyncio.run(service.run_once())
    assert summary["emails_sent"] == 0
    processor.process.assert_not_awaited()


def test_low_quality_result_is_checkpointed_without_email():
    db = Db()
    service, _, processor = make_service(db, [repo("1")], results={"1": processor_result("1", decision="IGNORE", email_status="NOT_SENT", candidate_id=None)})
    summary = asyncio.run(service.run_once())
    assert summary["emails_sent"] == 0
    assert len(db.github_automation_state.records) == 1


def test_one_repository_failure_does_not_stop_remaining_repositories():
    db = Db()
    service, _, processor = make_service(db, [repo("1"), repo("2")], errors={"1": RuntimeError("first failed")})
    summary = asyncio.run(service.run_once())
    assert summary["repositories_checked"] == 2
    assert len(summary["errors"]) == 1
    assert processor.process.await_count == 2
    assert any(item.get("github_repo_id") == "2" for item in db.github_automation_state.records)


def test_discovery_failure_preserves_previous_checkpoint():
    db = Db()
    previous = {"github_repo_id": "1", "last_processed_activity_key": "1:old"}
    db.github_automation_state.records.append(previous.copy())
    service, github, _ = make_service(db, [])
    github.discover_repositories.side_effect = RuntimeError("GitHub unavailable")
    summary = asyncio.run(service.run_once())
    assert summary["status"] == "FAILED"
    assert db.github_automation_state.records[0]["last_processed_activity_key"] == "1:old"


def test_successful_checkpoint_contains_required_activity_state():
    db = Db()
    service, _, _ = make_service(db, [repo("1")])
    asyncio.run(service.run_once())
    state = db.github_automation_state.records[0]
    assert state["github_repo_id"] == "1"
    assert state["last_seen_pushed_at"] is not None
    assert state["last_processed_activity_key"].startswith("1:")
    assert state["last_successful_check_at"] is not None
    assert state["last_processing_status"] == "COMPLETED"


def test_ollama_unavailable_result_still_checkpoints_review():
    db = Db()
    service, _, processor = make_service(db, [repo("1")], results={"1": processor_result("1", decision="REVIEW", email_status="NOT_SENT")})
    summary = asyncio.run(service.run_once())
    assert summary["status"] == "COMPLETED"
    assert len(db.github_automation_state.records) == 1
    assert processor.process.await_count == 1


def test_email_failure_does_not_advance_activity_checkpoint():
    db = Db()
    service, _, _ = make_service(db, [repo("1")], results={"1": processor_result("1", email_status="FAILED")})
    summary = asyncio.run(service.run_once())
    assert summary["status"] == "COMPLETED"
    assert summary["errors"]
    assert db.github_automation_state.records[0]["last_processing_status"] == "FAILED"
    assert "last_processed_activity_key" not in db.github_automation_state.records[0]


def test_repeated_run_is_idempotent():
    db = Db()
    service, _, processor = make_service(db, [repo("1")])
    asyncio.run(service.run_once())
    asyncio.run(service.run_once())
    assert processor.process.await_count == 1
    assert len(db.github_automation_state.records) == 1


def test_failure_logs_do_not_expose_credentials(caplog):
    db = Db()
    service, _, _ = make_service(db, [repo("1")], errors={"1": RuntimeError("token=secret-token password=secret-password mongodb://user:pass@example.invalid")})
    with caplog.at_level("WARNING"):
        asyncio.run(service.run_once())
    assert "secret-token" not in caplog.text
    assert "secret-password" not in caplog.text
    assert "mongodb://user:pass" not in caplog.text
