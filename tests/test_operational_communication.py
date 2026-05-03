import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as presensi


@pytest.fixture()
def communication_db(tmp_path, monkeypatch):
    db_path = tmp_path / "communication.db"
    monkeypatch.setattr(presensi, "DB_PATH", str(db_path))
    monkeypatch.setenv("FLASK_SECRET", "test-secret-communication")
    presensi._init_db()
    return db_path


def _seed_communication_data(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO users (id, email, name, role, password_hash, is_active, tier, created_at)
            VALUES
                (1, 'employee@test.local', 'Employee', 'employee', 'hash', 1, 'basic', '2026-01-01 00:00:00'),
                (2, 'supervisor@test.local', 'Supervisor', 'supervisor', 'hash', 1, 'pro', '2026-01-01 00:00:00'),
                (3, 'admin@test.local', 'Admin', 'hr_superadmin', 'hash', 1, 'enterprise', '2026-01-01 00:00:00'),
                (4, 'employee2@test.local', 'Employee Two', 'employee', 'hash', 1, 'basic', '2026-01-01 00:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO clients (
                id, name, address, office_email, office_phone,
                pic_name, pic_title, pic_phone, created_at
            ) VALUES (1, 'Acme', 'Jakarta', 'ops@acme.test', '021', 'PIC', 'Ops', '0812', '2026-01-01 00:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO sites (id, client_id, name, is_active, created_at)
            VALUES
                (1, 1, 'Site A', 1, '2026-01-01 00:00:00'),
                (2, 1, 'Site B', 1, '2026-01-01 00:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO shifts (id, name, start_time, end_time, is_active, created_at)
            VALUES (1, 'Morning', '08:00', '17:00', 1, '2026-01-01 00:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO assignments (
                employee_user_id, client_id, site_id, shift_id, start_date, status, created_at
            ) VALUES
                (1, 1, 1, 1, '2026-04-01', 'ACTIVE', '2026-04-01 00:00:00'),
                (4, 1, 2, 1, '2026-04-01', 'ACTIVE', '2026-04-01 00:00:00')
            """
        )
        conn.execute(
            "INSERT INTO supervisor_sites (supervisor_user_id, site_id) VALUES (2, 1)"
        )
        conn.commit()
    finally:
        conn.close()


def _employee_session(client) -> None:
    with client.session_transaction() as sess:
        sess["user"] = {
            "id": 1,
            "email": "employee@test.local",
            "role": "employee",
            "name": "Employee",
            "tier": "basic",
        }
        sess["csrf_token"] = "csrf-test-token"


def _supervisor_session(client) -> None:
    with client.session_transaction() as sess:
        sess["user"] = {
            "id": 2,
            "email": "supervisor@test.local",
            "role": "supervisor",
            "name": "Supervisor",
            "tier": "pro",
        }
        sess["csrf_token"] = "csrf-test-token"


def _admin_session(client) -> None:
    with client.session_transaction() as sess:
        sess["user"] = {
            "id": 3,
            "email": "admin@test.local",
            "role": "hr_superadmin",
            "name": "Admin",
            "tier": "enterprise",
        }
        sess["csrf_token"] = "csrf-test-token"


def _enable_communication_stack(*, tier: str = "enterprise") -> None:
    global_addons = [
        presensi.ADDON_COMMUNICATION_CHAT,
        presensi.ADDON_COMMUNICATION_ANNOUNCEMENT,
        presensi.ADDON_COMMUNICATION_INCIDENT,
    ]
    presensi._set_global_addons(global_addons)
    presensi._set_communication_client_config(
        1,
        enabled=True,
        tier=tier,
        message_limit_per_day=300,
        attachment_limit_mb=5,
    )


def test_chat_rooms_auto_created_and_message_flow_works(communication_db):
    _seed_communication_data(communication_db)
    _enable_communication_stack()
    flask_app = presensi.create_app()
    flask_app.config.update(TESTING=True)

    with flask_app.test_client() as client:
        _employee_session(client)
        rooms_response = client.get("/api/chat/list")
        assert rooms_response.status_code == 200
        rooms = rooms_response.get_json()["data"]
        room_types = {room["type"] for room in rooms}
        assert {"site", "shift", "role", "private"} <= room_types

        site_room = next(room for room in rooms if room["type"] == "site")
        send_response = client.post(
            "/api/chat/send",
            json={"room_id": site_room["id"], "message": "Update patroli selesai."},
            headers={"X-CSRF-Token": "csrf-test-token"},
        )
        assert send_response.status_code == 200

    with flask_app.test_client() as client:
        _supervisor_session(client)
        rooms_response = client.get("/api/chat/list")
        assert rooms_response.status_code == 200
        rooms = rooms_response.get_json()["data"]
        site_room = next(room for room in rooms if room["type"] == "site")
        assert site_room["unread_count"] >= 1

        room_response = client.get(f"/api/chat/room/{site_room['id']}")
        assert room_response.status_code == 200
        messages = room_response.get_json()["data"]
        assert any(message["message"] == "Update patroli selesai." for message in messages)


def test_announcement_create_list_and_read_flow(communication_db):
    _seed_communication_data(communication_db)
    _enable_communication_stack()
    flask_app = presensi.create_app()
    flask_app.config.update(TESTING=True)

    with flask_app.test_client() as client:
        _admin_session(client)
        create_response = client.post(
            "/api/announcement/create",
            json={
                "title": "Briefing Site",
                "message": "Kumpul 10 menit sebelum shift.",
                "target_type": "site",
                "target_id": "1",
                "is_mandatory": True,
            },
            headers={"X-CSRF-Token": "csrf-test-token"},
        )
        assert create_response.status_code == 200

    with flask_app.test_client() as client:
        _employee_session(client)
        list_response = client.get("/api/announcement/list")
        assert list_response.status_code == 200
        announcements = list_response.get_json()["data"]
        assert len(announcements) == 1
        assert announcements[0]["title"] == "Briefing Site"
        assert announcements[0]["read_at"] is None

        read_response = client.post(
            "/api/announcement/read",
            json={"announcement_id": announcements[0]["id"]},
            headers={"X-CSRF-Token": "csrf-test-token"},
        )
        assert read_response.status_code == 200

        list_again = client.get("/api/announcement/list")
        updated = list_again.get_json()["data"][0]
        assert updated["read_at"] is not None


def test_admin_communication_page_renders(communication_db):
    _seed_communication_data(communication_db)
    _enable_communication_stack()
    flask_app = presensi.create_app()
    flask_app.config.update(TESTING=True)

    with flask_app.test_client() as client:
        _admin_session(client)
        response = client.get("/dashboard/admin/communication")
        assert response.status_code == 200
        html = response.get_data(as_text=True)

    assert "Operational Communication" in html
    assert "Create Announcement" in html
    assert "Live Chat" in html
    assert "Feed, Monitor & History" in html
    assert "Client Communication Control" in html
    assert "Pilih client" in html
    assert "Pilih site" in html
    assert ">Basic<" not in html


def test_incident_create_list_and_auto_room_flow(communication_db):
    _seed_communication_data(communication_db)
    _enable_communication_stack()
    flask_app = presensi.create_app()
    flask_app.config.update(TESTING=True)

    with flask_app.test_client() as client:
        _employee_session(client)
        create_response = client.post(
            "/api/incident/create",
            data={
                "title": "Gate Timur Terbuka",
                "description": "Pintu akses timur tidak menutup otomatis setelah kendaraan masuk.",
                "csrf_token": "csrf-test-token",
            },
            headers={"X-CSRF-Token": "csrf-test-token"},
        )
        assert create_response.status_code == 200
        payload = create_response.get_json()["data"]
        assert payload["chat_room_id"] > 0

        incident_response = client.get("/api/incident/list")
        assert incident_response.status_code == 200
        incidents = incident_response.get_json()["data"]
        assert len(incidents) == 1
        assert incidents[0]["title"] == "Gate Timur Terbuka"

    with flask_app.test_client() as client:
        _supervisor_session(client)
        rooms_response = client.get("/api/chat/list")
        rooms = rooms_response.get_json()["data"]
        assert any(room["type"] == "incident" for room in rooms)

        room_id = next(room["id"] for room in rooms if room["type"] == "incident")
        room_response = client.get(f"/api/chat/room/{room_id}")
        assert room_response.status_code == 200
        messages = room_response.get_json()["data"]
        assert any("Gate Timur Terbuka" in message["message"] for message in messages)


def test_chat_room_and_incident_isolated_by_site_scope(communication_db):
    _seed_communication_data(communication_db)
    _enable_communication_stack()
    flask_app = presensi.create_app()
    flask_app.config.update(TESTING=True)

    with flask_app.test_client() as client:
        _employee_session(client)
        client.post(
            "/api/incident/create",
            data={
                "title": "Generator Drop",
                "description": "Tegangan genset turun sementara saat pergantian shift.",
                "csrf_token": "csrf-test-token",
            },
            headers={"X-CSRF-Token": "csrf-test-token"},
        )

    with flask_app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {
                "id": 4,
                "email": "employee2@test.local",
                "role": "employee",
                "name": "Employee Two",
                "tier": "basic",
            }
            sess["csrf_token"] = "csrf-test-token"
        incident_response = client.get("/api/incident/list")
        incidents = incident_response.get_json()["data"]
        assert incidents == []

        room_response = client.get("/api/chat/list")
        rooms = room_response.get_json()["data"]
        assert all(room["type"] != "incident" for room in rooms)


def test_chat_send_has_basic_rate_limit(communication_db):
    _seed_communication_data(communication_db)
    _enable_communication_stack()
    flask_app = presensi.create_app()
    flask_app.config.update(TESTING=True)

    with flask_app.test_client() as client:
        _employee_session(client)
        rooms_response = client.get("/api/chat/list")
        site_room = next(room for room in rooms_response.get_json()["data"] if room["type"] == "site")
        for index in range(8):
            response = client.post(
                "/api/chat/send",
                json={"room_id": site_room["id"], "message": f"Ping {index}"},
                headers={"X-CSRF-Token": "csrf-test-token"},
            )
            assert response.status_code == 200

        blocked = client.post(
            "/api/chat/send",
            json={"room_id": site_room["id"], "message": "Ping blocked"},
            headers={"X-CSRF-Token": "csrf-test-token"},
        )
        assert blocked.status_code == 429


def test_shift_room_thread_reply_and_delete_flow(communication_db):
    _seed_communication_data(communication_db)
    _enable_communication_stack()
    flask_app = presensi.create_app()
    flask_app.config.update(TESTING=True)

    with flask_app.test_client() as client:
        _employee_session(client)
        rooms_response = client.get("/api/chat/list")
        rooms = rooms_response.get_json()["data"]
        shift_room = next(room for room in rooms if room["type"] == "shift")

        create_thread = client.post(
            "/api/chat/thread/create",
            json={"room_id": shift_room["id"], "title": "Serah terima pagi"},
            headers={"X-CSRF-Token": "csrf-test-token"},
        )
        assert create_thread.status_code == 200
        thread_id = create_thread.get_json()["data"]["id"]

        reply_response = client.post(
            "/api/chat/thread/reply",
            json={"room_id": shift_room["id"], "thread_id": thread_id, "message": "Checklist area loading dock aman."},
            headers={"X-CSRF-Token": "csrf-test-token"},
        )
        assert reply_response.status_code == 200
        message_id = reply_response.get_json()["data"]["id"]

        threads_response = client.get(f"/api/chat/room/{shift_room['id']}/threads")
        assert threads_response.status_code == 200
        threads = threads_response.get_json()["data"]
        assert any(thread["id"] == thread_id for thread in threads)

        delete_response = client.post(
            "/api/chat/message/delete",
            json={"message_id": message_id},
            headers={"X-CSRF-Token": "csrf-test-token"},
        )
        assert delete_response.status_code == 200

    conn = sqlite3.connect(communication_db)
    try:
        audit_row = conn.execute(
            """
            SELECT action
            FROM audit_logs
            WHERE entity_type = 'chat_message'
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()
        assert audit_row is not None
        assert audit_row[0] == "DELETE"
    finally:
        conn.close()


def test_employee_dashboard_communication_section_renders(communication_db):
    _seed_communication_data(communication_db)
    _enable_communication_stack()
    flask_app = presensi.create_app()
    flask_app.config.update(TESTING=True)

    with flask_app.test_client() as client:
        _employee_session(client)
        response = client.get("/dashboard/pegawai")
        assert response.status_code == 200
        html = response.get_data(as_text=True)

    assert "Komunikasi" in html
    assert "Laporkan Kejadian" in html
    assert "Incident Aktif" in html


def test_communication_site_disable_blocks_incident(communication_db):
    _seed_communication_data(communication_db)
    presensi._set_global_addons([
        presensi.ADDON_COMMUNICATION_CHAT,
        presensi.ADDON_COMMUNICATION_ANNOUNCEMENT,
        presensi.ADDON_COMMUNICATION_INCIDENT,
    ])
    presensi._set_communication_site_config(
        1,
        enabled=False,
        message_limit_per_day=300,
        attachment_limit_mb=5,
    )
    flask_app = presensi.create_app()
    flask_app.config.update(TESTING=True)

    with flask_app.test_client() as client:
        _employee_session(client)
        response = client.post(
            "/api/incident/create",
            data={
                "title": "Site Communication Block",
                "description": "Tidak boleh lolos saat communication pada site dimatikan.",
                "csrf_token": "csrf-test-token",
            },
            headers={"X-CSRF-Token": "csrf-test-token"},
        )
        assert response.status_code == 403


def test_communication_endpoint_no_longer_accepts_api_token_auth(communication_db):
    _seed_communication_data(communication_db)
    _enable_communication_stack()
    flask_app = presensi.create_app()
    flask_app.config.update(TESTING=True)

    with flask_app.test_client() as client:
        response = client.get("/api/chat/list", headers={"X-API-Key": "fake-token"})
        assert response.status_code == 403


def test_owner_communication_dependencies_auto_enable_chat(communication_db):
    _seed_communication_data(communication_db)
    presensi._set_global_addons([
        presensi.ADDON_COMMUNICATION_ANNOUNCEMENT,
        presensi.ADDON_COMMUNICATION_INCIDENT,
    ])
    presensi._set_communication_client_config(
        1,
        enabled=True,
        tier="enterprise",
        message_limit_per_day=300,
        attachment_limit_mb=5,
    )
    config = presensi._communication_client_config(1)
    assert config["owner_chat_enabled"] is True
    assert config["enabled"] is True

    flask_app = presensi.create_app()
    flask_app.config.update(TESTING=True)

    with flask_app.test_client() as client:
        _employee_session(client)
        response = client.get("/api/chat/list")
        assert response.status_code == 200
