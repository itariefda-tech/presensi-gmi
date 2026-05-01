import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as presensi


@pytest.fixture()
def flow_db(tmp_path, monkeypatch):
    db_path = tmp_path / "flow.db"
    monkeypatch.setattr(presensi, "DB_PATH", str(db_path))
    presensi._init_db()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO clients (
                id, name, address, office_email, office_phone,
                pic_name, pic_title, pic_phone, created_at
            ) VALUES (1, 'Client A', 'Jakarta', 'client@test.local', '021',
                'PIC', 'Ops', '0812', '2026-05-01 08:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO sites (id, client_id, name, is_active, created_at)
            VALUES (10, 1, 'Site A', 1, '2026-05-01 08:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO clients (
                id, name, address, office_email, office_phone,
                pic_name, pic_title, pic_phone, created_at
            ) VALUES (2, 'Client B', 'Bandung', 'clientb@test.local', '022',
                'PIC B', 'Ops', '0813', '2026-05-01 08:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO sites (id, client_id, name, is_active, created_at)
            VALUES (20, 2, 'Site B', 1, '2026-05-01 08:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO users (id, email, name, role, password_hash, is_active, tier, created_at)
            VALUES
                (100, 'emp@test.local', 'Employee', 'employee', 'x', 1, 'enterprise', '2026-05-01 08:00:00'),
                (200, 'admin@test.local', 'Admin', 'hr_superadmin', 'x', 1, 'enterprise', '2026-05-01 08:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO employees (
                id, nik, name, email, no_hp, address, gender, status_nikah,
                is_active, site_id, client_id, branch_id, created_at
            ) VALUES (300, 'NIK300', 'Employee', 'emp@test.local', '0812',
                'Jakarta', 'L', 'single', 1, 10, 1, 10, '2026-05-01 08:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO assignments (
                id, employee_user_id, client_id, site_id, branch_id,
                start_date, status, created_at
            ) VALUES (400, 100, 1, 10, 10, '2026-05-01', 'ACTIVE', '2026-05-01 08:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO assignments (
                id, employee_user_id, client_id, site_id, branch_id,
                start_date, status, created_at
            ) VALUES (401, 100, 2, 20, 20, '2026-05-01', 'ENDED', '2026-05-01 08:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO patrol_routes (
                id, client_id, site_id, name, scan_mode, strict_mode, is_active, created_at
            ) VALUES (500, 1, 10, 'Route A', 'nfc', 1, 1, '2026-05-01 08:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO patrol_checkpoints (
                id, route_id, site_id, sequence_no, sequence_order, name, nfc_tag,
                latitude, longitude, radius_meters, is_active, created_at
            ) VALUES
                (501, 500, 10, 1, 1, 'CP 1', 'CP1', 0, 0, 50, 1, '2026-05-01 08:00:00'),
                (502, 500, 10, 2, 2, 'CP 2', 'CP2', 0, 0, 50, 1, '2026-05-01 08:00:00')
            """
        )
        conn.commit()
    finally:
        conn.close()
    return db_path


def test_leave_uses_assignment_relation_and_locks_final_status(flow_db):
    leave_id = presensi._create_leave_request(
        employee_email="emp@test.local",
        employee_id=300,
        employee_user_id=100,
        assignment_id=400,
        client_id=1,
        site_id=10,
        leave_type="izin",
        date_from="2026-05-01",
        date_to="2026-05-01",
        reason="Keperluan keluarga",
        attachment=None,
        attachment_path=None,
    )
    admin = presensi.User(id=200, email="admin@test.local", role="hr_superadmin")

    record = presensi._get_leave_request_by_id(leave_id)
    assert record["employee_id"] == 300
    assert record["assignment_id"] == 400
    assert record["site_id"] == 10

    assert presensi._update_leave_request_status(leave_id, "approved", admin, None) is True
    assert presensi._update_leave_request_status(leave_id, "rejected", admin, "late") is False

    approved = presensi._get_leave_request_by_id(leave_id)
    assert approved["status"] == "approved"
    assert approved["approved_by_id"] == 200
    assert approved["approved_by_role"] == "hr_superadmin"


def test_duplicate_leave_request_is_rejected_atomically(flow_db):
    kwargs = dict(
        employee_email="emp@test.local",
        employee_id=300,
        employee_user_id=100,
        assignment_id=400,
        client_id=1,
        site_id=10,
        leave_type="izin",
        date_from="2026-05-02",
        date_to="2026-05-02",
        reason="Keperluan keluarga",
        attachment=None,
        attachment_path=None,
    )
    presensi._create_leave_request(**kwargs)
    with pytest.raises(presensi.DuplicateSubmissionError):
        presensi._create_leave_request(**kwargs)


def test_leave_snapshot_survives_employee_reassignment(flow_db):
    leave_id = presensi._create_leave_request(
        employee_email="emp@test.local",
        employee_id=300,
        employee_user_id=100,
        assignment_id=400,
        client_id=1,
        site_id=10,
        leave_type="izin",
        date_from="2026-05-03",
        date_to="2026-05-03",
        reason="Urusan keluarga",
        attachment=None,
        attachment_path=None,
    )
    conn = sqlite3.connect(flow_db)
    try:
        conn.execute("UPDATE assignments SET client_id = 2, site_id = 20 WHERE id = 400")
        conn.commit()
        row = conn.execute(
            "SELECT client_id_snapshot, site_id_snapshot FROM leave_requests WHERE id = ?",
            (leave_id,),
        ).fetchone()
        assert row == (1, 10)
    finally:
        conn.close()


def test_patrol_ops_writes_report_and_locks_closed_status(flow_db):
    user = presensi.User(id=100, email="emp@test.local", role="employee")
    reviewer = presensi.User(id=200, email="admin@test.local", role="hr_superadmin")
    employee = {"id": 300, "name": "Employee"}
    assignment = {"id": 400, "site_id": 10}
    site = {"id": 10, "client_id": 1, "name": "Site A"}

    event_id = presensi._insert_patrol_ops_event(
        category="incident",
        event_type="incident",
        severity="critical",
        direction="",
        vehicle_plate="",
        vehicle_type="",
        note="Incident critical",
        checklist=[],
        photo_path="",
        lat=None,
        lng=None,
        user=user,
        employee=employee,
        assignment=assignment,
        site=site,
    )
    report_id = presensi._create_patrol_report_from_event(
        event_id=event_id,
        user=user,
        employee=employee,
        assignment=assignment,
        site=site,
        category="incident",
        severity="critical",
        note="Incident critical",
        photo_path="",
    )
    presensi._sync_patrol_report_status_from_event(event_id, "resolved", reviewer)

    conn = sqlite3.connect(flow_db)
    try:
        report = conn.execute("SELECT * FROM patrol_reports WHERE id = ?", (report_id,)).fetchone()
        assert report[3] == 100
        assert report[4] == 400
        assert report[6] == 1
        assert report[12] == "closed"
    finally:
        conn.close()

    assert presensi._patrol_ops_status_transition_allowed("resolved", "reviewed") is False


def test_patrol_ops_update_is_compare_and_set(flow_db):
    user = presensi.User(id=100, email="emp@test.local", role="employee")
    reviewer = presensi.User(id=200, email="admin@test.local", role="hr_superadmin")
    event_id = presensi._insert_patrol_ops_event(
        category="activity",
        event_type="round",
        severity="low",
        direction="",
        vehicle_plate="",
        vehicle_type="",
        note="Routine check",
        checklist=[],
        photo_path="",
        lat=None,
        lng=None,
        user=user,
        employee={"id": 300, "name": "Employee"},
        assignment={"id": 400, "site_id": 10},
        site={"id": 10, "client_id": 1, "name": "Site A"},
    )
    assert presensi._update_patrol_ops_event_status(event_id, "reviewed", "", reviewer, "open") is True
    assert presensi._update_patrol_ops_event_status(event_id, "resolved", "", reviewer, "open") is False


def test_duplicate_patrol_ops_report_is_rejected(flow_db):
    user = presensi.User(id=100, email="emp@test.local", role="employee")
    payload = dict(
        category="activity",
        event_type="round",
        severity="low",
        direction="",
        vehicle_plate="",
        vehicle_type="",
        note="Duplicate check",
        checklist=[],
        photo_path="",
        lat=None,
        lng=None,
        user=user,
        employee={"id": 300, "name": "Employee"},
        assignment={"id": 400, "site_id": 10},
        site={"id": 10, "client_id": 1, "name": "Site A"},
    )
    presensi._insert_patrol_ops_event(**payload)
    with pytest.raises(presensi.DuplicateSubmissionError):
        presensi._insert_patrol_ops_event(**payload)


def test_patrol_ops_query_respects_client_scope(flow_db):
    user = presensi.User(id=100, email="emp@test.local", role="employee")
    presensi._insert_patrol_ops_event(
        category="activity",
        event_type="client-a",
        severity="low",
        direction="",
        vehicle_plate="",
        vehicle_type="",
        note="Client A event",
        checklist=[],
        photo_path="",
        lat=None,
        lng=None,
        user=user,
        employee={"id": 300, "name": "Employee"},
        assignment={"id": 400, "site_id": 10},
        site={"id": 10, "client_id": 1, "name": "Site A"},
    )
    presensi._insert_patrol_ops_event(
        category="activity",
        event_type="client-b",
        severity="low",
        direction="",
        vehicle_plate="",
        vehicle_type="",
        note="Client B event",
        checklist=[],
        photo_path="",
        lat=None,
        lng=None,
        user=user,
        employee={"id": 300, "name": "Employee"},
        assignment={"id": 401, "site_id": 20},
        site={"id": 20, "client_id": 2, "name": "Site B"},
    )
    rows = presensi._patrol_ops_events(client_id=1)
    assert {row["client_id"] for row in rows} == {1}


def test_attendance_stores_policy_snapshot(flow_db):
    record = presensi._create_attendance_record(
        employee={"id": 300, "name": "Employee"},
        employee_email="emp@test.local",
        action="checkin",
        method="gps",
        device_time="1999-01-01T00:00:00Z",
        source="app",
        assignment={"id": 400, "client_id": 1, "site_id": 10},
        site={"id": 10, "client_id": 1},
        policy={"policy_id": 9, "allow_gps": 1, "require_selfie": 0},
        accuracy="7",
    )
    conn = sqlite3.connect(flow_db)
    try:
        row = conn.execute(
            "SELECT assignment_id, site_id, client_id, policy_snapshot, device_time FROM attendance WHERE id = ?",
            (record["id"],),
        ).fetchone()
        assert row[0:3] == (400, 10, 1)
        assert '"policy_id": 9' in row[3]
        assert row[4] == "1999-01-01T00:00:00Z"
    finally:
        conn.close()


def test_guard_tour_syncs_session_and_logs(flow_db):
    user = presensi.User(id=100, email="emp@test.local", role="employee")
    route = {"id": 500, "client_id": 1, "scan_mode": "qr", "strict_mode": 1}
    assignment = {"id": 400, "site_id": 10, "shift_id": None}
    employee = {"id": 300}

    tour = presensi._create_patrol_tour(
        route=route,
        assignment=assignment,
        employee=employee,
        user=user,
        total_checkpoints=2,
    )
    tour_id = int(tour["id"])
    presensi._insert_patrol_scan(
        tour_id=tour_id,
        route_id=500,
        employee_email="emp@test.local",
        checkpoint_id=None,
        checkpoint_sequence=1,
        expected_sequence=1,
        is_expected_sequence=True,
        method="qr",
        scan_payload="CP1",
        timestamp_value="2026-05-01 09:00:00",
        lat=None,
        lng=None,
        gps_distance_m=None,
        gps_valid=True,
        selfie_path=None,
        selfie_required=False,
        selfie_valid=True,
        interval_seconds=None,
        validation_status=presensi.PATROL_SCAN_VALID,
        validation_note=None,
    )

    conn = sqlite3.connect(flow_db)
    try:
        session = conn.execute("SELECT assignment_id, site_id, status FROM patrol_sessions WHERE id = ?", (tour_id,)).fetchone()
        log = conn.execute("SELECT session_id, status FROM patrol_logs WHERE session_id = ?", (tour_id,)).fetchone()
        assert session == (400, 10, presensi.PATROL_STATUS_ONGOING)
        assert log == (tour_id, "valid")
    finally:
        conn.close()


def test_guard_tour_rejects_skip_sequence(flow_db, monkeypatch):
    monkeypatch.setenv("FLASK_SECRET", "test-secret-flow")
    presensi._set_global_addons([presensi.ADDON_PATROL])
    conn = sqlite3.connect(flow_db)
    try:
        conn.execute(
            """
            INSERT INTO attendance (
                employee_id, client_id, branch_id, employee_name, employee_email,
                date, time, action, method, source, created_at
            ) VALUES (300, 1, 10, 'Employee', 'emp@test.local', ?, '08:00',
                'checkin', 'gps', 'test', '2026-05-01 08:00:00')
            """,
            (presensi._today_key(),),
        )
        conn.commit()
    finally:
        conn.close()

    flask_app = presensi.create_app()
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as client:
        with client.session_transaction() as sess:
            sess["csrf_token"] = "csrf-test-token"
            sess["user"] = {
                "id": 100,
                "email": "emp@test.local",
                "role": "employee",
                "name": "Employee",
                "tier": "enterprise",
                "client_id": 1,
                "site_id": 10,
            }
        start = client.post("/api/patrol/start", data={"csrf_token": "csrf-test-token"})
        assert start.status_code == 200
        tour_id = start.get_json()["data"]["tour"]["id"]
        skipped = client.post(
            "/api/patrol/scan",
            data={
                "csrf_token": "csrf-test-token",
                "tour_id": str(tour_id),
                "method": "nfc",
                "scan_data": "CP2",
                "lat": "0",
                "lng": "0",
            },
        )
        assert skipped.status_code == 400
        assert "Urutan checkpoint salah" in skipped.get_json()["message"]
