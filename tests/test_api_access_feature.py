import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as presensi


@pytest.fixture()
def api_access_db(tmp_path, monkeypatch):
    db_path = tmp_path / "api_access.db"
    monkeypatch.setattr(presensi, "DB_PATH", str(db_path))
    monkeypatch.setenv("FLASK_SECRET", "test-secret-api-access")
    monkeypatch.setattr(presensi, "OWNER_ADDON_PASSWORD", "owner-pass")
    presensi._init_db()
    return db_path


def _seed_api_access_data(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO users (
                id, email, name, role, password_hash, is_active,
                tier, created_at, client_id, site_id
            ) VALUES (1, 'admin@test.local', 'Admin', 'hr_superadmin',
                'hash', 1, 'enterprise', '2026-01-01 00:00:00', NULL, NULL)
            """
        )
        conn.execute(
            """
            INSERT INTO users (
                id, email, name, role, password_hash, is_active,
                tier, created_at, client_id, site_id
            ) VALUES
                (100, 'emp1@acme.test', 'Employee A', 'employee', 'hash', 1, 'basic', '2026-01-01 00:00:00', 1, 1),
                (200, 'emp2@bravo.test', 'Employee B', 'employee', 'hash', 1, 'basic', '2026-01-01 00:00:00', 2, 2)
            """
        )
        conn.execute(
            """
            INSERT INTO clients (
                id, name, address, office_email, office_phone,
                pic_name, pic_title, pic_phone, created_at
            ) VALUES
                (1, 'Acme', 'Jakarta', 'finance@acme.test', '021', 'PIC', 'Finance', '0812', '2026-01-01 00:00:00'),
                (2, 'Bravo', 'Bandung', 'finance@bravo.test', '022', 'PIC', 'Finance', '0813', '2026-01-01 00:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO sites (id, client_id, name, is_active, created_at)
            VALUES
                (1, 1, 'Site A', 1, '2026-01-01 00:00:00'),
                (2, 2, 'Site B', 1, '2026-01-01 00:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO assignments (
                employee_user_id, client_id, site_id, start_date, status, created_at
            ) VALUES
                (100, 1, 1, '2026-04-01', 'ACTIVE', '2026-04-01 00:00:00'),
                (200, 2, 2, '2026-04-01', 'ACTIVE', '2026-04-01 00:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO attendance (
                employee_id, client_id, branch_id, employee_name, employee_email,
                date, time, action, method, created_at
            ) VALUES
                (100, 1, 1, 'Employee A', 'emp1@acme.test', '2026-04-10', '08:00', 'checkin', 'qr', '2026-04-10 08:00:00'),
                (200, 2, 2, 'Employee B', 'emp2@bravo.test', '2026-04-10', '08:00', 'checkin', 'qr', '2026-04-10 08:00:00')
            """
        )
        conn.commit()
    finally:
        conn.close()


def _admin_session(client) -> None:
    with client.session_transaction() as sess:
        sess["user"] = {
            "id": 1,
            "email": "admin@test.local",
            "role": "hr_superadmin",
            "name": "Admin",
            "tier": "enterprise",
        }
        sess["csrf_token"] = "csrf-test-token"


def test_owner_api_access_toggle_can_be_unlocked_and_saved(api_access_db):
    flask_app = presensi.create_app()
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as client:
        with client.session_transaction() as sess:
            sess["csrf_token"] = "csrf-test-token"

        locked = client.get("/api/owner/addons")
        assert locked.status_code == 200
        assert locked.get_json()["data"]["addons"] == []

        verified = client.post(
            "/api/owner/addons/verify",
            json={"password": "owner-pass"},
            headers={"X-CSRF-Token": "csrf-test-token"},
        )
        assert verified.status_code == 200

        enabled = client.post(
            "/api/owner/addons",
            json={"addons": [presensi.ADDON_API_ACCESS]},
            headers={"X-CSRF-Token": "csrf-test-token"},
        )
        assert enabled.status_code == 200
        assert presensi.ADDON_API_ACCESS in enabled.get_json()["data"]["addons"]

        disabled = client.post(
            "/api/owner/addons",
            json={"addons": []},
            headers={"X-CSRF-Token": "csrf-test-token"},
        )
        assert disabled.status_code == 200
        assert presensi.ADDON_API_ACCESS not in disabled.get_json()["data"]["addons"]


def test_subscription_update_requires_owner_toggle_for_api_access(api_access_db):
    _seed_api_access_data(api_access_db)
    flask_app = presensi.create_app()
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as client:
        _admin_session(client)

        locked = client.post(
            "/dashboard/admin/settings/subscription/update",
            data={
                "csrf_token": "csrf-test-token",
                "client_id": "1",
                "package_type": "ENTERPRISE",
                "addons": [presensi.ADDON_API_ACCESS],
            },
        )
        assert locked.status_code == 302
        assert presensi.ADDON_API_ACCESS not in presensi._list_client_addons(1)

        presensi._set_global_addons([presensi.ADDON_API_ACCESS])
        unlocked = client.post(
            "/dashboard/admin/settings/subscription/update",
            data={
                "csrf_token": "csrf-test-token",
                "client_id": "1",
                "package_type": "ENTERPRISE",
                "addons": [presensi.ADDON_API_ACCESS],
            },
        )
        assert unlocked.status_code == 302
        assert presensi.ADDON_API_ACCESS in presensi._list_client_addons(1)


def test_subscription_update_keeps_other_addons_when_api_access_toggled(api_access_db):
    _seed_api_access_data(api_access_db)
    presensi._set_global_addons([presensi.ADDON_API_ACCESS])
    flask_app = presensi.create_app()
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as client:
        _admin_session(client)

        first = client.post(
            "/dashboard/admin/settings/subscription/update",
            data={
                "csrf_token": "csrf-test-token",
                "client_id": "1",
                "package_type": "ENTERPRISE",
                "addons": [presensi.ADDON_API_ACCESS, presensi.ADDON_BILLING_ENGINE],
            },
        )
        assert first.status_code == 302
        assert set(presensi._list_client_addons(1)) == {presensi.ADDON_API_ACCESS, presensi.ADDON_BILLING_ENGINE}

        second = client.post(
            "/dashboard/admin/settings/subscription/update",
            data={
                "csrf_token": "csrf-test-token",
                "client_id": "1",
                "package_type": "ENTERPRISE",
                "addons": [presensi.ADDON_BILLING_ENGINE],
            },
        )
        assert second.status_code == 302
        assert set(presensi._list_client_addons(1)) == {presensi.ADDON_BILLING_ENGINE}


def test_owner_toggle_keeps_other_global_addons_when_api_access_changes(api_access_db):
    flask_app = presensi.create_app()
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as client:
        with client.session_transaction() as sess:
            sess["csrf_token"] = "csrf-test-token"

        client.post(
            "/api/owner/addons/verify",
            json={"password": "owner-pass"},
            headers={"X-CSRF-Token": "csrf-test-token"},
        )
        client.post(
            "/api/owner/addons",
            json={"addons": [presensi.ADDON_PATROL, presensi.ADDON_API_ACCESS]},
            headers={"X-CSRF-Token": "csrf-test-token"},
        )
        response = client.post(
            "/api/owner/addons",
            json={"addons": [presensi.ADDON_PATROL]},
            headers={"X-CSRF-Token": "csrf-test-token"},
        )
        assert response.status_code == 200
        saved = set(response.get_json()["data"]["addons"])
        assert presensi.ADDON_PATROL in saved
        assert presensi.ADDON_API_ACCESS not in saved


def test_enterprise_bundle_auto_enables_all_owner_addons(api_access_db):
    presensi._set_global_addons([presensi.ADDON_ENTERPRISE_TIER])

    saved = set(presensi._global_addons())
    assert presensi.ADDON_ENTERPRISE_TIER in saved
    assert presensi.ADDON_API_ACCESS in saved
    assert presensi.ADDON_REPORTING_ADVANCED in saved
    assert presensi.ADDON_BILLING_ENGINE in saved
    assert presensi.ADDON_CONTRACT_MANAGEMENT in saved


def test_api_access_token_is_hashed_and_can_access_scoped_attendance(api_access_db):
    _seed_api_access_data(api_access_db)
    presensi._set_global_addons([presensi.ADDON_API_ACCESS])
    presensi._set_client_package(1, "ENTERPRISE")
    presensi._set_client_addons(1, [presensi.ADDON_API_ACCESS])
    token_row, plain_token = presensi._generate_client_api_token(1, "ERP Integration")

    conn = sqlite3.connect(api_access_db)
    conn.row_factory = sqlite3.Row
    try:
        stored = conn.execute("SELECT token_hash, token_prefix FROM api_client_tokens WHERE id = ?", (token_row["id"],)).fetchone()
    finally:
        conn.close()

    assert plain_token not in stored["token_hash"]
    assert stored["token_hash"] == presensi._hash_token(plain_token)
    assert stored["token_prefix"] == plain_token[: presensi.API_ACCESS_TOKEN_PREFIX_LENGTH]

    flask_app = presensi.create_app()
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as client:
        invalid = client.get(
            "/api/v1/attendance?client_id=1",
            headers={"X-API-Key": "invalid-token"},
        )
        assert invalid.status_code == 401

        scoped = client.get(
            "/api/v1/attendance?client_id=2&employee_email=emp2@bravo.test&from=2026-04-10&to=2026-04-10",
            headers={"X-API-Key": plain_token},
        )
        assert scoped.status_code == 403

        success = client.get(
            "/api/v1/attendance?client_id=2&site_id=1&employee_email=emp1@acme.test&from=2026-04-10&to=2026-04-10",
            headers={"X-API-Key": plain_token},
        )
        assert success.status_code == 200
        payload = success.get_json()["data"]
        assert payload["client_id"] == 1
        assert payload["site_id"] == 1
        assert len(payload["records"]) == 1
        record_email = payload["records"][0].get("employee_email") or payload["records"][0].get("email")
        assert record_email == "emp1@acme.test"

    summary = presensi._api_access_dashboard_summary(1)
    assert summary["token_count"] == 1
    assert summary["last_call"]["endpoint"] == "/api/v1/attendance"
    assert summary["top_endpoint"]["endpoint"] == "/api/v1/attendance"


def test_api_access_returns_403_when_client_addon_is_off(api_access_db):
    _seed_api_access_data(api_access_db)
    presensi._set_global_addons([presensi.ADDON_API_ACCESS])
    token_row, plain_token = presensi._generate_client_api_token(1, "ERP Integration")
    assert token_row["id"] > 0

    flask_app = presensi.create_app()
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as client:
        blocked = client.get(
            "/api/v1/attendance?client_id=1&from=2026-04-10&to=2026-04-10",
            headers={"X-API-Key": plain_token},
        )
        assert blocked.status_code == 403


def test_api_access_site_scope_does_not_leak_other_client_site(api_access_db):
    _seed_api_access_data(api_access_db)
    presensi._set_global_addons([presensi.ADDON_API_ACCESS])
    presensi._set_client_package(1, "ENTERPRISE")
    presensi._set_client_addons(1, [presensi.ADDON_API_ACCESS])
    _, plain_token = presensi._generate_client_api_token(1, "ERP Integration")

    flask_app = presensi.create_app()
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as client:
        blocked = client.get(
            "/api/v1/attendance?client_id=1&site_id=2&from=2026-04-10&to=2026-04-10",
            headers={"X-API-Key": plain_token},
        )
        assert blocked.status_code == 400


def test_revoked_api_access_token_cannot_be_used(api_access_db):
    _seed_api_access_data(api_access_db)
    presensi._set_global_addons([presensi.ADDON_API_ACCESS])
    presensi._set_client_package(1, "ENTERPRISE")
    presensi._set_client_addons(1, [presensi.ADDON_API_ACCESS])
    token_row, plain_token = presensi._generate_client_api_token(1, "ERP Integration")

    flask_app = presensi.create_app()
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as client:
        _admin_session(client)
        revoked = client.post(
            f"/dashboard/admin/settings/subscription/1/api-access/token/{token_row['id']}/revoke",
            data={"csrf_token": "csrf-test-token"},
        )
        assert revoked.status_code == 302

    assert presensi._list_api_client_tokens(1) == []

    flask_app = presensi.create_app()
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as client:
        blocked = client.get(
            "/api/v1/attendance?client_id=1",
            headers={"X-API-Key": plain_token},
        )
        assert blocked.status_code == 401


def test_subscription_page_can_filter_usage_log_by_date(api_access_db):
    _seed_api_access_data(api_access_db)
    presensi._set_global_addons([presensi.ADDON_API_ACCESS])
    presensi._set_client_package(1, "ENTERPRISE")
    presensi._set_client_addons(1, [presensi.ADDON_API_ACCESS])
    token_row, _ = presensi._generate_client_api_token(1, "ERP Integration")
    conn = sqlite3.connect(api_access_db)
    try:
        conn.execute(
            """
            INSERT INTO api_access_logs (
                client_id, token_id, token_label, endpoint, http_method,
                status_code, actor_type, actor_email, branch_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (1, token_row["id"], "ERP Integration", "/api/v1/attendance", "GET", 200, "token", None, 1, "2026-04-10 08:00:00"),
        )
        conn.execute(
            """
            INSERT INTO api_access_logs (
                client_id, token_id, token_label, endpoint, http_method,
                status_code, actor_type, actor_email, branch_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (1, token_row["id"], "ERP Integration", "/api/v1/other", "GET", 200, "token", None, 1, "2026-04-12 09:00:00"),
        )
        conn.commit()
    finally:
        conn.close()

    flask_app = presensi.create_app()
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as client:
        _admin_session(client)
        response = client.get("/dashboard/admin/settings?tab=subscription&api_log_from=2026-04-10&api_log_to=2026-04-10")
        assert response.status_code == 200
        html = response.get_data(as_text=True)

    assert "/api/v1/attendance" in html
    assert "/api/v1/other" not in html


def test_api_access_migration_is_safe_to_rerun(api_access_db):
    _seed_api_access_data(api_access_db)
    presensi._set_global_addons([presensi.ADDON_API_ACCESS])
    presensi._set_client_package(1, "ENTERPRISE")
    presensi._set_client_addons(1, [presensi.ADDON_API_ACCESS])
    token_row, plain_token = presensi._generate_client_api_token(1, "ERP Integration")

    presensi._init_db()
    presensi._init_db()

    assert presensi.ADDON_API_ACCESS in presensi._list_client_addons(1)
    tokens = presensi._list_api_client_tokens(1, include_revoked=True)
    assert len(tokens) == 1
    assert tokens[0]["id"] == token_row["id"]
    assert presensi._api_access_token_lookup(plain_token)["id"] == token_row["id"]
