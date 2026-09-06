from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from backend.server import app


TRIGGER = "trigger-secret-for-test"


def test_weekly_trigger_missing_secret_is_rejected():
    with patch("backend.routes.admin_processing.get_settings", return_value={}):
        response = TestClient(app).post("/api/admin/weekly-github-discovery")
    assert response.status_code == 401


def test_weekly_trigger_wrong_secret_is_rejected():
    with patch("backend.routes.admin_processing.get_settings", return_value={"github_automation_trigger_secret": TRIGGER}):
        response = TestClient(app).post(
            "/api/admin/weekly-github-discovery",
            headers={"X-Admin-Secret": "wrong"},
        )
    assert response.status_code == 401


def test_weekly_trigger_requires_dedicated_secret_only():
    client = TestClient(app)
    for settings, secret in [
        ({"admin_secret": TRIGGER}, TRIGGER),
        ({"approval_secret": TRIGGER}, TRIGGER),
        ({"github_automation_trigger_secret": TRIGGER}, TRIGGER),
    ]:
        with patch("backend.routes.admin_processing.get_settings", return_value=settings), patch(
            "backend.routes.admin_processing.automation_enabled", return_value=False
        ):
            response = client.post("/api/admin/weekly-github-discovery", headers={"X-Admin-Secret": secret})
        if "github_automation_trigger_secret" in settings:
            assert response.status_code == 200
        else:
            assert response.status_code == 401


def test_weekly_trigger_fallback_secrets_do_not_authenticate():
    client = TestClient(app)
    for settings in ({"admin_secret": TRIGGER}, {"approval_secret": TRIGGER}):
        with patch("backend.routes.admin_processing.get_settings", return_value=settings):
            response = client.post(
                "/api/admin/weekly-github-discovery",
                headers={"X-Admin-Secret": TRIGGER},
            )
        assert response.status_code == 401


def test_weekly_trigger_disabled_does_not_run_automation():
    with patch("backend.routes.admin_processing.get_settings", return_value={"github_automation_trigger_secret": TRIGGER}), \
         patch("backend.routes.admin_processing.automation_enabled", return_value=False), \
         patch("backend.routes.admin_processing.GitHubWeeklyAutomationService") as service_class:
        response = TestClient(app).post(
            "/api/admin/weekly-github-discovery",
            headers={"X-Admin-Secret": TRIGGER},
        )

    assert response.status_code == 200
    assert response.json() == {"status": "disabled"}
    service_class.assert_not_called()


def test_weekly_trigger_enabled_invokes_existing_service_and_returns_summary():
    summary = {
        "run_id": "run-test",
        "status": "COMPLETED",
        "repositories_checked": 2,
        "new_repositories_detected": 1,
        "updated_repositories_detected": 1,
        "candidates_created_or_updated": 1,
        "emails_sent": 1,
        "errors": [],
    }
    with patch("backend.routes.admin_processing.get_settings", return_value={"github_automation_trigger_secret": TRIGGER}), \
         patch("backend.routes.admin_processing.automation_enabled", return_value=True), \
         patch("backend.routes.admin_processing.GitHubWeeklyAutomationService") as service_class:
        service_class.return_value.run_once = AsyncMock(return_value=summary)
        response = TestClient(app).post(
            "/api/admin/weekly-github-discovery",
            headers={"X-Admin-Secret": TRIGGER},
        )

    assert response.status_code == 200
    assert response.json() == summary
    service_class.return_value.run_once.assert_awaited_once()
    assert TRIGGER not in response.text


def test_workflow_has_weekly_schedule_dispatch_secret_and_render_endpoint():
    from pathlib import Path

    workflow = Path(".github/workflows/weekly-github-automation.yml").read_text()
    assert 'cron: "0 3 * * 0"' in workflow
    assert "workflow_dispatch:" in workflow
    assert "secrets.GITHUB_AUTOMATION_TRIGGER_SECRET" in workflow
    assert "https://portfolio-ps-43gi.onrender.com/api/admin/weekly-github-discovery" in workflow
    assert "MONGO_URL" not in workflow
    assert "RESEND_API_KEY" not in workflow
    assert "APPROVAL_SECRET" not in workflow
    assert "ADMIN_SECRET" not in workflow
