from __future__ import annotations

import smtplib
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.models.candidate import CandidateRecord
from backend.server import app
from backend.services.approval_service import ApprovalService
from backend.services.approval_token_service import ApprovalTokenError, ApprovalTokenService
from backend.services.email_service import EmailDeliveryError, EmailService


class InMemoryCandidates:
    def __init__(self, candidate):
        self.candidate = candidate
        self.update_calls = []

    async def find_one(self, query):
        if query.get("candidate_id") == self.candidate.get("candidate_id"):
            return dict(self.candidate)
        return None

    async def update_one(self, query, update):
        self.update_calls.append(update)
        self.candidate.update(update.get("$set", {}))
        if "$inc" in update:
            for key, value in update["$inc"].items():
                self.candidate[key] = self.candidate.get(key, 0) + value


@pytest.fixture
def candidate():
    return {
        "candidate_id": "candidate-phase5",
        "candidate_status": "CANDIDATE",
        "recommendation": "CANDIDATE",
        "repository_name": "CareerMitra",
        "suggested_title": "CareerMitra",
        "suggested_description": "A career planning tool.",
        "overall_score": 88,
        "candidate_priority": 91,
        "portfolio_fit_score": 86,
        "duplicate_risk": "LOW",
        "differentiation_reason": "Adds a distinct workflow.",
        "scores": {"technical_depth": 88, "originality": 84, "impact": 82, "portfolio_fit": 86},
        "evidence": ["Repository contains a tested API"],
        "consumed_approval_token_ids": [],
        "email_status": "NOT_SENT",
        "email_send_count": 0,
    }


def test_token_creation_validation_and_opaque_candidate_id():
    service = ApprovalTokenService(secret="phase5-test-secret", ttl_seconds=3600)
    token = service.create_token("candidate-secret-id", "APPROVE")
    assert "candidate-secret-id" not in token
    payload = service.decode_token(token)
    assert payload["cid"] == "candidate-secret-id"
    assert payload["act"] == "APPROVE"


def test_expired_invalid_and_wrong_action_tokens():
    service = ApprovalTokenService(secret="phase5-test-secret", ttl_seconds=60)
    old = datetime.now(timezone.utc) - timedelta(minutes=5)
    expired = service.create_token("candidate-1", "APPROVE", now=old)
    with pytest.raises(ApprovalTokenError, match="expired"):
        service.decode_token(expired, now=datetime.now(timezone.utc))
    with pytest.raises(ApprovalTokenError, match="Invalid"):
        service.decode_token("not-a-token")
    valid = service.create_token("candidate-1", "APPROVE")
    with pytest.raises(ApprovalTokenError, match="different action"):
        service.decode_token(valid, expected_action="REJECT")


@pytest.mark.asyncio
@pytest.mark.parametrize("action,target", [("APPROVE", "APPROVED"), ("REJECT", "REJECTED"), ("REVIEW", "REVIEW")])
async def test_candidate_state_transitions_and_metadata(candidate, action, target):
    db = MagicMock()
    db.candidates = InMemoryCandidates(candidate)
    service = ApprovalService(ApprovalTokenService(secret="phase5-test-secret"))
    token = service.token_service.create_token(candidate["candidate_id"], action)

    result = await service.apply(db, token)

    assert result["status"] == "processed"
    assert db.candidates.candidate["candidate_status"] == target
    assert db.candidates.candidate["decision"] == target
    assert db.candidates.candidate["decision_source"] == "EMAIL"
    assert db.candidates.candidate["approval_token_version"] == "v1"


@pytest.mark.asyncio
async def test_already_processed_token_is_safe(candidate):
    db = MagicMock()
    db.candidates = InMemoryCandidates(candidate)
    service = ApprovalService(ApprovalTokenService(secret="phase5-test-secret"))
    token = service.token_service.create_token(candidate["candidate_id"], "APPROVE")

    first = await service.apply(db, token)
    second = await service.apply(db, token)

    assert first["status"] == "processed"
    assert second["status"] == "already_processed"
    assert len(db.candidates.update_calls) == 1


@pytest.mark.asyncio
async def test_invalid_state_does_not_transition(candidate):
    candidate["candidate_status"] = "APPROVED"
    db = MagicMock()
    db.candidates = InMemoryCandidates(candidate)
    service = ApprovalService(ApprovalTokenService(secret="phase5-test-secret"))
    token = service.token_service.create_token(candidate["candidate_id"], "REJECT")

    result = await service.apply(db, token)

    assert result["status"] == "already_processed"
    assert not db.candidates.update_calls


def test_approval_endpoints_and_result_are_safe(monkeypatch, candidate):
    monkeypatch.setenv("APPROVAL_SECRET", "phase5-test-secret")
    db = MagicMock()
    db.candidates = InMemoryCandidates(candidate)
    token = ApprovalTokenService(secret="phase5-test-secret").create_token(candidate["candidate_id"], "APPROVE")
    with patch("backend.routes.approval.get_database", return_value=db):
        client = TestClient(app)
        preview = client.get(f"/api/approval/{token}")
        assert preview.status_code == 200
        assert preview.json()["action"] == "APPROVE"
        response = client.post(f"/api/approval/{token}", json={"action": "APPROVE"})
        assert response.status_code == 200
        assert response.json()["status"] == "processed"
        replay = client.post(f"/api/approval/{token}", json={"action": "APPROVE"})
        assert replay.status_code == 200
        assert replay.json()["status"] == "already_processed"
        invalid = client.get("/api/approval/not-a-token")
        assert invalid.status_code == 400
        assert "candidate-phase5" not in invalid.text


def test_email_service_success_and_failure(candidate):
    settings = {
        "email_provider": "smtp",
        "email_from": "owner@example.com",
        "email_to": "owner@example.com",
        "email_host": "smtp.example.com",
        "email_port": "587",
        "frontend_base_url": "https://portfolio.example.com",
        "approval_secret": "phase5-test-secret",
        "approval_token_ttl_hours": "48",
    }
    service = EmailService(settings=settings, token_service=ApprovalTokenService(secret="phase5-test-secret"))
    with patch.object(service, "_send_message") as send:
        result = __import__("asyncio").run(service.send_candidate_email(candidate))
        assert send.called
        assert set(result["tokens"]) == {"APPROVE", "REJECT", "REVIEW"}
        message = send.call_args.args[0]
        plain_body = message.get_body(preferencelist=("plain",)).get_content()
        assert "CareerMitra" in plain_body
        assert "10,000" not in plain_body

    with patch.object(service, "_send_message", side_effect=smtplib.SMTPException("private smtp detail")):
        with pytest.raises(EmailDeliveryError, match="Email delivery failed"):
            try:
                __import__("asyncio").run(service.send_candidate_email(candidate))
            except EmailDeliveryError as error:
                assert isinstance(error.__cause__, smtplib.SMTPException)
                raise


def test_email_template_contains_repository_and_decision_links(candidate):
    candidate["full_name"] = "Heetshah21/igniteHackathon404Found"
    service = EmailService(settings={"frontend_base_url": "https://portfolio.example.com"}, token_service=ApprovalTokenService(secret="phase5-test-secret"))
    links = {action: f"https://portfolio.example.com/approval/token-{action.lower()}" for action in ("APPROVE", "REJECT", "REVIEW")}
    message = service._build_message(candidate, links, "sender@example.com", "recipient@example.com")
    body = "\n".join(part.get_content() for part in message.walk() if part.get_content_type() in {"text/plain", "text/html"})

    assert candidate["suggested_title"] in body
    assert candidate["full_name"] in body
    assert "YES - ADD TO PORTFOLIO" in body
    assert "NO - REJECT" in body
    assert "REVIEW LATER" in body
    assert body.count("/approval/") == 6


def test_send_email_endpoint_success_failure_and_duplicate(candidate):
    db = MagicMock()
    db.candidates = InMemoryCandidates(candidate)
    with patch("backend.routes.candidates.get_database", return_value=db), patch("backend.routes.candidates.EmailService") as email_class:
        email_class.return_value.send_candidate_email = AsyncMock(return_value={"tokens": {}})
        client = TestClient(app)
        sent = client.post(f"/api/candidates/{candidate['candidate_id']}/send-email")
        assert sent.status_code == 200
        assert sent.json()["status"] == "sent"
        assert db.candidates.candidate["email_status"] == "SENT"
        duplicate = client.post(f"/api/candidates/{candidate['candidate_id']}/send-email")
        assert duplicate.status_code == 200
        assert duplicate.json()["status"] == "already_sent"
        assert email_class.return_value.send_candidate_email.await_count == 1

    candidate["email_status"] = "NOT_SENT"
    with patch("backend.routes.candidates.get_database", return_value=db), patch("backend.routes.candidates.EmailService") as email_class:
        email_class.return_value.send_candidate_email = AsyncMock(side_effect=EmailDeliveryError("Email delivery failed"))
        failed = TestClient(app).post(f"/api/candidates/{candidate['candidate_id']}/send-email")
        assert failed.status_code == 502
        assert failed.json()["detail"] == "Email delivery failed"
        assert db.candidates.candidate["email_status"] == "FAILED"


def test_send_email_failure_logs_safe_smtp_context_without_lifecycle_side_effects(candidate, caplog):
    db = MagicMock()
    db.candidates = InMemoryCandidates(candidate)
    with patch("backend.routes.candidates.get_database", return_value=db), \
         patch("backend.routes.candidates.EmailService") as email_class, \
         patch("backend.routes.candidates.get_settings", return_value={
             "email_provider": "smtp",
             "email_host": "smtp.example.com",
             "email_port": "587",
             "email_use_tls": "true",
         }):
        delivery_error = EmailDeliveryError("Email delivery failed")
        delivery_error.__cause__ = smtplib.SMTPAuthenticationError(535, b"password=do-not-log token=secret-token")
        email_class.return_value.send_candidate_email = AsyncMock(side_effect=delivery_error)
        with caplog.at_level("ERROR"):
            response = TestClient(app).post(f"/api/candidates/{candidate['candidate_id']}/send-email")

    assert response.status_code == 502
    assert "exception_type=SMTPAuthenticationError" in caplog.text
    assert "exception_type=EmailDeliveryError" not in caplog.text
    assert "provider=smtp" in caplog.text
    assert "host=smtp.example.com" in caplog.text
    assert "port=587" in caplog.text
    assert "tls=true" in caplog.text
    assert "do-not-log" not in caplog.text
    assert "secret-token" not in caplog.text
    assert candidate["suggested_title"] not in caplog.text
    assert candidate["suggested_description"] not in caplog.text
    assert db.candidates.candidate["candidate_status"] == "CANDIDATE"


def test_candidate_model_preserves_phase5_metadata(candidate):
    record = CandidateRecord(**candidate)
    assert record.candidate_priority == 91
    assert record.email_status == "NOT_SENT"
    assert record.consumed_approval_token_ids == []
