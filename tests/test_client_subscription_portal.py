import os
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as presensi


@pytest.fixture()
def client_portal_db(tmp_path, monkeypatch):
    db_path = tmp_path / "client_portal.db"
    monkeypatch.setattr(presensi, "DB_PATH", str(db_path))
    monkeypatch.setenv("FLASK_SECRET", "test-secret-client-portal")
    presensi._init_db()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO clients (
                id, name, address, office_email, office_phone, pic_name, pic_title, pic_phone, created_at, updated_at,
                communication_enabled, communication_tier,
                communication_message_limit_per_day, communication_attachment_limit_mb
            ) VALUES (
                1, 'Acme Client', 'Jakarta', 'ops@acme.test', '021', 'PIC Acme', 'Manager', '0812', '2026-01-01 00:00:00', '2026-01-01 00:00:00',
                1, 'pro_plus', 250, 8
            )
            """
        )
        conn.execute(
            """
            INSERT INTO sites (
                id, client_id, name, address, latitude, longitude, radius_meters,
                is_active, created_at, updated_at
            ) VALUES (
                1, 1, 'Site Alpha', 'Jakarta Pusat', -6.2, 106.8, 100,
                1, '2026-01-01 00:00:00', '2026-01-01 00:00:00'
            )
            """
        )
        conn.execute(
            """
            INSERT INTO users (
                id, email, name, role, password_hash, is_active, tier,
                client_id, site_id, created_at
            ) VALUES (
                1, 'clientadmin@acme.test', 'Client Admin', 'client_admin',
                'hash', 1, 'pro', 1, 1, '2026-01-01 00:00:00'
            )
            """
        )
        conn.commit()
    finally:
        conn.close()
    presensi._set_global_addons([
        presensi.ADDON_HRIS_PRO_PLUS,
        presensi.ADDON_API_ACCESS,
        presensi.ADDON_COMMUNICATION_CHAT,
        presensi.ADDON_COMMUNICATION_ANNOUNCEMENT,
    ])
    presensi._set_client_package(1, presensi.CLIENT_PACKAGE_ENTERPRISE)
    presensi._set_client_addons(1, [
        presensi.ADDON_API_ACCESS,
        presensi.ADDON_PATROL,
        presensi.ADDON_CALENDAR,
        presensi.ADDON_PAYROLL_PLUS,
    ])
    yield db_path


def _client_admin_session(client):
    with client.session_transaction() as sess:
        sess["user"] = {
            "id": 1,
            "email": "clientadmin@acme.test",
            "role": "client_admin",
            "name": "Client Admin",
            "tier": "pro",
            "client_id": 1,
            "site_id": 1,
        }
        sess["csrf_token"] = "csrf-client-token"


def test_client_dashboard_renders_subscription_access_panel(client_portal_db):
    flask_app = presensi.create_app()
    flask_app.config.update(TESTING=True)

    with flask_app.test_client() as client:
        _client_admin_session(client)
        response = client.get("/dashboard/client?pane=6")
        assert response.status_code == 200
        html = response.get_data(as_text=True)

    assert "Subscription & Access" in html
    assert "API Credentials" in html
    assert 'data-initial-tab="6"' in html
    assert "Recent API Usage" in html


def test_client_admin_can_generate_and_revoke_api_token_from_client_dashboard(client_portal_db):
    flask_app = presensi.create_app()
    flask_app.config.update(TESTING=True)

    with flask_app.test_client() as client:
        _client_admin_session(client)
        create_response = client.post(
            "/client/subscription/api-token/create",
            data={"csrf_token": "csrf-client-token", "label": "ERP Client"},
            follow_redirects=True,
        )
        assert create_response.status_code == 200
        html = create_response.get_data(as_text=True)
        assert "Token API berhasil dibuat." in html
        assert "ERP Client" in html

    conn = sqlite3.connect(client_portal_db)
    try:
        token_row = conn.execute(
            "SELECT id, revoked_at FROM api_client_tokens WHERE client_id = 1 ORDER BY id DESC LIMIT 1"
        ).fetchone()
        assert token_row is not None
        token_id = int(token_row[0])
        assert token_row[1] is None
    finally:
        conn.close()

    with flask_app.test_client() as client:
        _client_admin_session(client)
        revoke_response = client.post(
            f"/client/subscription/api-token/{token_id}/revoke",
            data={"csrf_token": "csrf-client-token"},
            follow_redirects=True,
        )
        assert revoke_response.status_code == 200
        assert "Token API dicabut." in revoke_response.get_data(as_text=True)

    conn = sqlite3.connect(client_portal_db)
    try:
        revoked_at = conn.execute(
            "SELECT revoked_at FROM api_client_tokens WHERE id = ?",
            (token_id,),
        ).fetchone()[0]
        assert revoked_at
    finally:
        conn.close()
