import os
import sqlite3
import uuid

import pytest

os.environ["FLASK_SECRET"] = "test-secret-for-ai-analysis-import-123456789"
_TEST_DB_DIR = os.path.join(os.getcwd(), ".pytest_cache", "ai_analysis")
os.makedirs(_TEST_DB_DIR, exist_ok=True)
os.environ["PRESENSI_DB_PATH"] = os.path.join(_TEST_DB_DIR, f"presensi-import-{uuid.uuid4().hex}.db")

import app as presensi_app


@pytest.fixture()
def ai_app(monkeypatch):
    db_path = os.path.join(_TEST_DB_DIR, f"presensi-test-{uuid.uuid4().hex}.db")
    monkeypatch.setenv("FLASK_SECRET", "test-secret-for-ai-analysis-123456789")
    monkeypatch.setattr(presensi_app, "DB_PATH", db_path)
    flask_app = presensi_app.create_app()
    flask_app.config.update(TESTING=True)
    with flask_app.app_context():
        presensi_app._set_global_addons([presensi_app.ADDON_AI])
        presensi_app._create_user(
            "HR Admin",
            "admin@example.com",
            "hr_superadmin",
            "secret123",
            tier="enterprise",
        )
    return flask_app


@pytest.fixture()
def logged_in_client(ai_app):
    client = ai_app.test_client()
    response = client.post(
        "/api/auth/login",
        json={"identifier": "admin@example.com", "password": "secret123"},
    )
    assert response.status_code == 200
    with client.session_transaction() as session:
        session["csrf_token"] = "test-csrf"
    return client


def test_ai_analysis_summary_endpoint_returns_predictive_payload(logged_in_client):
    response = logged_in_client.get("/api/admin/ai-analysis/summary?start_date=2026-04-01&end_date=2026-04-28")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert "summary" in payload["data"]
    assert payload["data"]["predictive_readiness"]["ml_enabled"] is False
    assert payload["data"]["fairness_notice"]


def test_ai_snapshot_stores_aggregate_and_employee_rows(ai_app):
    with ai_app.app_context():
        employee_id = presensi_app._create_user(
            "Field Employee",
            "field@example.com",
            "employee",
            "secret123",
        )
        filters = {"start_date": "2026-04-01", "end_date": "2026-04-28", "client_id": None, "site_id": None}
        payload = {
            "summary": {"period": "2026-04-01 to 2026-04-28"},
            "insights": [],
            "risks": [],
            "recommendations": ["Monitor rutin."],
            "alerts": [],
            "rule_version": presensi_app.AI_ANALYSIS_RULE_VERSION,
            "employee_analysis": [
                {
                    "employee_email": "field@example.com",
                    "employee_name": "Field Employee",
                    "work_days": 20,
                    "present_days": 18,
                    "late_days": 2,
                    "unexcused_absent_days": 1,
                    "total_late_minutes": 15,
                    "early_leave_days": 0,
                    "missing_checkout_days": 1,
                    "attendance_rate": 90.0,
                    "absence_rate": 5.0,
                    "discipline_score": 84.2,
                    "discipline_grade": "B",
                    "discipline_category": "Stable Discipline",
                    "insight": "Disiplin pegawai masih stabil.",
                    "recommendations": ["Coaching ringan."],
                }
            ],
        }

        snapshot_id = presensi_app._save_ai_analysis_snapshot(filters, payload, user_id=None)

    conn = sqlite3.connect(os.fspath(ai_app.config.get("DATABASE", presensi_app.DB_PATH)))
    try:
        conn.row_factory = sqlite3.Row
        aggregate = conn.execute(
            "SELECT * FROM ai_analysis_snapshots WHERE id = ? AND employee_id IS NULL",
            (snapshot_id,),
        ).fetchone()
        employee = conn.execute(
            "SELECT * FROM ai_analysis_snapshots WHERE employee_id = ?",
            (employee_id,),
        ).fetchone()
    finally:
        conn.close()

    assert aggregate is not None
    assert employee is not None
    assert employee["late_days"] == 2
    assert employee["grade"] == "B"
    assert employee["recommendation_text"] == "Coaching ringan."
