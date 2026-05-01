import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as presensi


@pytest.fixture()
def payroll_db(tmp_path, monkeypatch):
    db_path = tmp_path / "payroll.db"
    monkeypatch.setattr(presensi, "DB_PATH", str(db_path))
    presensi._init_db()
    return db_path


def _seed_employee_policy(db_path, *, schedule: str, scheme: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO clients (
                id, name, address, office_email, office_phone,
                pic_name, pic_title, pic_phone, created_at
            ) VALUES (1, 'Client A', 'Jakarta', 'hr@client.test', '021',
                'PIC', 'HR', '0812', '2026-01-01 00:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO sites (id, client_id, name, address, is_active, created_at)
            VALUES (1, 1, 'Site A', 'Jakarta', 1, '2026-01-01 00:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO users (
                id, email, name, role, password_hash, is_active,
                client_id, site_id, tier, created_at
            ) VALUES (1, 'employee@test.local', 'Employee One', 'employee',
                'hash', 1, 1, 1, 'pro', '2026-01-01 00:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO employees (
                id, nik, name, email, no_hp, address, gender,
                status_nikah, is_active, client_id, site_id, created_at
            ) VALUES (1, 'EMP001', 'Employee One', 'employee@test.local',
                '0812', 'Jakarta', 'M', 'single', 1, 1, 1, '2026-01-01 00:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO assignments (
                id, employee_user_id, client_id, site_id, start_date,
                end_date, status, created_at
            ) VALUES (1, 1, 1, 1, '2026-01-01', NULL, 'ACTIVE',
                '2026-01-01 00:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO attendance_policies (
                id, scope_type, client_id, site_id, effective_from,
                payroll_scheme, payroll_schedule, cutoff_time, grace_minutes,
                created_at
            ) VALUES (1, 'SITE', 1, 1, '2026-01-01', ?, ?, '09:00', 0,
                '2026-01-01 00:00:00')
            """,
            (scheme, schedule),
        )
        conn.commit()
    finally:
        conn.close()


def _insert_checkins(db_path, dates: list[str]) -> None:
    conn = sqlite3.connect(db_path)
    try:
        for idx, date_key in enumerate(dates, start=1):
            conn.execute(
                """
                INSERT INTO attendance (
                    employee_id, client_id, branch_id, employee_name,
                    employee_email, date, time, action, method, source, created_at
                ) VALUES (1, 1, 1, 'Employee One', 'employee@test.local',
                    ?, '08:00', 'checkin', 'gps', 'app', ?)
                """,
                (date_key, f"{date_key} 08:00:{idx:02d}"),
            )
        conn.commit()
    finally:
        conn.close()


def _seed_second_site_employee(db_path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO sites (id, client_id, name, address, is_active, created_at)
            VALUES (2, 1, 'Site B', 'Bandung', 1, '2026-01-01 00:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO users (
                id, email, name, role, password_hash, is_active,
                client_id, site_id, tier, created_at
            ) VALUES (2, 'employee2@test.local', 'Employee Two', 'employee',
                'hash', 1, 1, 2, 'pro', '2026-01-01 00:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO employees (
                id, nik, name, email, no_hp, address, gender,
                status_nikah, is_active, client_id, site_id, created_at
            ) VALUES (2, 'EMP002', 'Employee Two', 'employee2@test.local',
                '0813', 'Bandung', 'F', 'single', 1, 1, 2, '2026-01-01 00:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO assignments (
                id, employee_user_id, client_id, site_id, start_date,
                end_date, status, created_at
            ) VALUES (2, 2, 1, 2, '2026-01-01', NULL, 'ACTIVE',
                '2026-01-01 00:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO attendance_policies (
                id, scope_type, client_id, site_id, effective_from,
                payroll_scheme, payroll_schedule, cutoff_time, grace_minutes,
                created_at
            ) VALUES (2, 'SITE', 1, 2, '2026-01-01',
                'PRORATED_ATTENDANCE', 'MID_MONTH', '09:00', 0,
                '2026-01-01 00:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO attendance (
                employee_id, client_id, branch_id, employee_name,
                employee_email, date, time, action, method, source, created_at
            ) VALUES (2, 1, 2, 'Employee Two', 'employee2@test.local',
                '2026-01-16', '08:00', 'checkin', 'gps', 'app',
                '2026-01-16 08:00:00')
            """
        )
        conn.commit()
    finally:
        conn.close()


def _seed_other_client_employee(db_path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO clients (
                id, name, address, office_email, office_phone,
                pic_name, pic_title, pic_phone, created_at
            ) VALUES (2, 'Client B', 'Surabaya', 'hr@clientb.test', '031',
                'PIC B', 'HR', '0814', '2026-01-01 00:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO sites (id, client_id, name, address, is_active, created_at)
            VALUES (3, 2, 'Site C', 'Surabaya', 1, '2026-01-01 00:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO users (
                id, email, name, role, password_hash, is_active,
                client_id, site_id, tier, created_at
            ) VALUES (3, 'employee3@test.local', 'Employee Three', 'employee',
                'hash', 1, 2, 3, 'pro', '2026-01-01 00:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO employees (
                id, nik, name, email, no_hp, address, gender,
                status_nikah, is_active, client_id, site_id, created_at
            ) VALUES (3, 'EMP003', 'Employee Three', 'employee3@test.local',
                '0814', 'Surabaya', 'M', 'single', 1, 2, 3, '2026-01-01 00:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO assignments (
                id, employee_user_id, client_id, site_id, start_date,
                end_date, status, created_at
            ) VALUES (3, 3, 2, 3, '2026-01-01', NULL, 'ACTIVE',
                '2026-01-01 00:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO attendance_policies (
                id, scope_type, client_id, site_id, effective_from,
                payroll_scheme, payroll_schedule, cutoff_time, grace_minutes,
                created_at
            ) VALUES (3, 'SITE', 2, 3, '2026-01-01',
                'PRORATED_ATTENDANCE', 'MID_MONTH', '09:00', 0,
                '2026-01-01 00:00:00')
            """
        )
        conn.commit()
    finally:
        conn.close()


def test_mid_month_pay_cycle_resolves_policy_period(payroll_db):
    _seed_employee_policy(
        payroll_db,
        schedule=presensi.PAYROLL_SCHEDULE_MID_MONTH,
        scheme=presensi.PAYROLL_SCHEME_PRORATED,
    )

    cycle = presensi._resolve_pay_cycle("employee@test.local", "2026-02")

    assert cycle["period_start"] == "2026-01-16"
    assert cycle["period_end"] == "2026-02-15"
    assert cycle["pay_date"] == "2026-02-16"
    assert cycle["payroll_schedule"] == presensi.PAYROLL_SCHEDULE_MID_MONTH
    assert cycle["payroll_scheme"] == presensi.PAYROLL_SCHEME_PRORATED


def test_policy_resolution_uses_site_client_global_order(payroll_db):
    _seed_employee_policy(
        payroll_db,
        schedule=presensi.PAYROLL_SCHEDULE_MID_MONTH,
        scheme=presensi.PAYROLL_SCHEME_PRORATED,
    )
    conn = sqlite3.connect(payroll_db)
    try:
        conn.execute(
            """
            INSERT INTO attendance_policies (
                id, scope_type, client_id, site_id, effective_from,
                payroll_scheme, payroll_schedule, cutoff_time, grace_minutes,
                created_at
            ) VALUES (4, 'CLIENT', 1, NULL, '2026-01-01',
                'FULL_MONTHLY_DEDUCTION', 'MONTH_END', '10:00', 0,
                '2026-01-01 00:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO attendance_policies (
                id, scope_type, client_id, site_id, effective_from,
                payroll_scheme, payroll_schedule, cutoff_time, grace_minutes,
                created_at
            ) VALUES (5, 'GLOBAL', NULL, NULL, '2026-01-01',
                'FULL_MONTHLY_DEDUCTION', 'MONTH_END', '11:00', 0,
                '2026-01-01 00:00:00')
            """
        )
        conn.commit()
    finally:
        conn.close()

    site_policy = presensi._resolve_attendance_policy(1, 1, None, "2026-02-01")
    assert site_policy["policy_id"] == 1
    assert site_policy["payroll_schedule"] == presensi.PAYROLL_SCHEDULE_MID_MONTH

    conn = sqlite3.connect(payroll_db)
    try:
        conn.execute("DELETE FROM attendance_policies WHERE id = 1")
        conn.commit()
    finally:
        conn.close()

    client_policy = presensi._resolve_attendance_policy(1, 1, None, "2026-02-01")
    assert client_policy["policy_id"] == 4
    assert client_policy["cutoff_time"] == "10:00"

    conn = sqlite3.connect(payroll_db)
    try:
        conn.execute("DELETE FROM attendance_policies WHERE id = 4")
        conn.commit()
    finally:
        conn.close()

    global_policy = presensi._resolve_attendance_policy(1, 1, None, "2026-02-01")
    assert global_policy["policy_id"] == 5
    assert global_policy["cutoff_time"] == "11:00"


def test_prorated_payroll_uses_only_attendance_inside_pay_cycle(payroll_db):
    _seed_employee_policy(
        payroll_db,
        schedule=presensi.PAYROLL_SCHEDULE_MID_MONTH,
        scheme=presensi.PAYROLL_SCHEME_PRORATED,
    )
    _insert_checkins(payroll_db, ["2026-01-15", "2026-01-16", "2026-02-15", "2026-02-16"])

    payroll = presensi._calculate_payroll("employee@test.local", "2026-02", 3100)

    assert payroll["period_start"] == "2026-01-16"
    assert payroll["period_end"] == "2026-02-15"
    assert payroll["working_days"] == 31
    assert payroll["attendance_days"] == 2
    assert payroll["potongan_absen"] == 0
    assert payroll["gross_salary"] == pytest.approx(200)
    assert payroll["total_gaji"] == pytest.approx(200)


def test_month_end_payroll_uses_calendar_month_window(payroll_db):
    _seed_employee_policy(
        payroll_db,
        schedule=presensi.PAYROLL_SCHEDULE_MONTH_END,
        scheme=presensi.PAYROLL_SCHEME_PRORATED,
    )
    _insert_checkins(payroll_db, ["2026-01-31", "2026-02-01", "2026-02-28", "2026-03-01"])

    payroll = presensi._calculate_payroll("employee@test.local", "2026-02", 2800)

    assert payroll["period_start"] == "2026-02-01"
    assert payroll["period_end"] == "2026-02-28"
    assert payroll["working_days"] == 28
    assert payroll["attendance_days"] == 2
    assert payroll["gross_salary"] == pytest.approx(200)


def test_full_monthly_payroll_keeps_base_and_deducts_absence(payroll_db):
    _seed_employee_policy(
        payroll_db,
        schedule=presensi.PAYROLL_SCHEDULE_MID_MONTH,
        scheme=presensi.PAYROLL_SCHEME_FULL_MONTHLY,
    )
    _insert_checkins(payroll_db, ["2026-01-16", "2026-02-15"])

    payroll = presensi._calculate_payroll("employee@test.local", "2026-02", 3100)

    assert payroll["working_days"] == 31
    assert payroll["attendance_days"] == 2
    assert payroll["absent_days"] == 29
    assert payroll["gross_salary"] == 3100
    assert payroll["potongan_absen"] == pytest.approx(2900)
    assert payroll["total_gaji"] == pytest.approx(200)


def test_created_payroll_persists_snapshot_and_matches_list(payroll_db):
    _seed_employee_policy(
        payroll_db,
        schedule=presensi.PAYROLL_SCHEDULE_MID_MONTH,
        scheme=presensi.PAYROLL_SCHEME_PRORATED,
    )
    _insert_checkins(payroll_db, ["2026-01-16", "2026-02-15"])

    payroll_id = presensi._create_payroll_record("employee@test.local", "2026-02", 3100)
    detail = presensi._get_payroll_by_id(payroll_id)
    rows = presensi._list_payroll_by_period("2026-02", client_id=1)

    assert detail is not None
    assert len(rows) == 1
    assert detail["period_start"] == "2026-01-16"
    assert detail["period_end"] == "2026-02-15"
    assert detail["site_id"] == 1
    assert detail["policy_id"] == 1
    assert detail["payroll_scheme"] == presensi.PAYROLL_SCHEME_PRORATED
    assert detail["calculation_version"] == presensi.PAYROLL_CALCULATION_VERSION
    assert rows[0]["site_id"] == 1
    assert rows[0]["total_gaji"] == detail["total_gaji"]


def test_legacy_payroll_null_snapshot_gets_safe_defaults(payroll_db):
    _seed_employee_policy(
        payroll_db,
        schedule=presensi.PAYROLL_SCHEDULE_MONTH_END,
        scheme=presensi.PAYROLL_SCHEME_PRORATED,
    )
    conn = sqlite3.connect(payroll_db)
    try:
        conn.execute(
            """
            INSERT INTO payroll (
                employee_id, client_id, branch_id, employee_email, period,
                salary_base, attendance_days, absent_days, leave_days,
                total_gaji, created_at
            ) VALUES (1, 1, 1, 'employee@test.local', '2026-02',
                2800, 2, 26, 0, 200, '2026-02-28 00:00:00')
            """
        )
        conn.commit()
    finally:
        conn.close()

    presensi._init_db()
    detail = presensi._get_payroll_by_employee_period("employee@test.local", "2026-02")

    assert detail is not None
    assert detail["working_days"] == 28
    assert detail["calculation_version"] == "legacy"
    assert detail["site_id"] == 1


def test_employee_summary_uses_pay_cycle_metadata(payroll_db):
    _seed_employee_policy(
        payroll_db,
        schedule=presensi.PAYROLL_SCHEDULE_MID_MONTH,
        scheme=presensi.PAYROLL_SCHEME_PRORATED,
    )
    _insert_checkins(payroll_db, ["2026-01-15", "2026-01-16", "2026-02-15", "2026-02-16"])

    user = presensi.User(id=1, email="employee@test.local", role="employee", client_id=1, site_id=1)
    summary = presensi._attendance_pay_cycle_summary_for_user(user, "2026-02")

    assert summary["summary_type"] == "pay_cycle"
    assert summary["period_start"] == "2026-01-16"
    assert summary["period_end"] == "2026-02-15"
    assert summary["payroll_schedule"] == presensi.PAYROLL_SCHEDULE_MID_MONTH
    assert summary["present"] == 2


def test_client_payroll_list_defaults_to_client_wide(payroll_db, monkeypatch):
    monkeypatch.setenv("FLASK_SECRET", "test-secret-for-payroll-list")
    _seed_employee_policy(
        payroll_db,
        schedule=presensi.PAYROLL_SCHEDULE_MID_MONTH,
        scheme=presensi.PAYROLL_SCHEME_PRORATED,
    )
    _seed_second_site_employee(payroll_db)
    _insert_checkins(payroll_db, ["2026-01-16"])
    presensi._create_payroll_record("employee@test.local", "2026-02", 3100)
    presensi._create_payroll_record("employee2@test.local", "2026-02", 3100)

    flask_app = presensi.create_app()
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {
                "id": 0,
                "email": "client@test.local",
                "role": "client_admin",
                "name": "Client Admin",
                "tier": "pro",
                "client_id": 1,
                "site_id": 1,
            }

        response = client.get("/api/payroll/list?period=2026-02")
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["ok"] is True
        assert {row["employee_email"] for row in payload["data"]} == {
            "employee@test.local",
            "employee2@test.local",
        }

        filtered = client.get("/api/payroll/list?period=2026-02&site_id=2")
        assert filtered.status_code == 200
        filtered_payload = filtered.get_json()
        assert [row["employee_email"] for row in filtered_payload["data"]] == ["employee2@test.local"]
        assert filtered_payload["data"][0]["site_id"] == 2

        schedule_filtered = client.get(
            "/api/payroll/list?period=2026-02&payroll_schedule=MONTH_END"
        )
        assert schedule_filtered.status_code == 200
        assert schedule_filtered.get_json()["data"] == []


def test_attendance_report_accepts_site_id_and_exposes_site_id(payroll_db, monkeypatch):
    monkeypatch.setenv("FLASK_SECRET", "test-secret-for-attendance-report-site")
    _seed_employee_policy(
        payroll_db,
        schedule=presensi.PAYROLL_SCHEDULE_MID_MONTH,
        scheme=presensi.PAYROLL_SCHEME_PRORATED,
    )
    _seed_second_site_employee(payroll_db)
    _insert_checkins(payroll_db, ["2026-01-16"])

    direct_rows = presensi._generate_attendance_report("2026-01-16", "2026-01-16", client_id=1, site_id=2)
    assert [row["employee_email"] for row in direct_rows] == ["employee2@test.local"]
    assert direct_rows[0]["site_id"] == 2

    flask_app = presensi.create_app()
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {
                "id": 0,
                "email": "admin@test.local",
                "role": "hr_superadmin",
                "name": "Admin",
                "tier": "pro",
            }

        response = client.get(
            "/api/reports/attendance?start_date=2026-01-16&end_date=2026-01-16&client_id=1&site_id=2"
        )
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["ok"] is True
        assert [row["employee_email"] for row in payload["data"]] == ["employee2@test.local"]
        assert payload["data"][0]["site_id"] == 2


def test_attendance_checkin_checkout_regression(payroll_db, monkeypatch):
    monkeypatch.setenv("FLASK_SECRET", "test-secret-for-attendance-flow")
    _seed_employee_policy(
        payroll_db,
        schedule=presensi.PAYROLL_SCHEDULE_MONTH_END,
        scheme=presensi.PAYROLL_SCHEME_PRORATED,
    )
    conn = sqlite3.connect(payroll_db)
    try:
        conn.execute("UPDATE sites SET latitude = 0, longitude = 0, radius_meters = 100 WHERE id = 1")
        conn.commit()
    finally:
        conn.close()

    flask_app = presensi.create_app()
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as client:
        with client.session_transaction() as sess:
            sess["csrf_token"] = "csrf-test-token"
            sess["user"] = {
                "id": 1,
                "email": "employee@test.local",
                "role": "employee",
                "name": "Employee One",
                "tier": "pro",
                "client_id": 1,
                "site_id": 1,
            }

        form = {
            "csrf_token": "csrf-test-token",
            "method": "gps",
            "lat": "0",
            "lng": "0",
        }
        checkin = client.post("/api/attendance/checkin", data=form)
        assert checkin.status_code == 200
        assert checkin.get_json()["data"]["action"] == "checkin"

        checkout = client.post("/api/attendance/checkout", data=form)
        assert checkout.status_code == 200
        assert checkout.get_json()["data"]["action"] == "checkout"


def test_advanced_reporting_endpoints_return_analytics(payroll_db, monkeypatch):
    monkeypatch.setenv("FLASK_SECRET", "test-secret-for-advanced-reporting")
    _seed_employee_policy(
        payroll_db,
        schedule=presensi.PAYROLL_SCHEDULE_MONTH_END,
        scheme=presensi.PAYROLL_SCHEME_PRORATED,
    )
    _insert_checkins(payroll_db, ["2026-01-16", "2026-01-17"])
    conn = sqlite3.connect(payroll_db)
    try:
        conn.execute("UPDATE sites SET latitude = 0, longitude = 0, radius_meters = 100 WHERE id = 1")
        conn.execute(
            """
            UPDATE attendance
            SET time = '10:00', late_flag = 1, lat = 0.01, lng = 0.01,
                gps_distance_m = 1572, inside_radius_flag = 0,
                near_radius_flag = 0, suspicious_location_flag = 1
            WHERE date = '2026-01-17'
            """
        )
        conn.execute(
            """
            INSERT INTO leave_requests (
                employee_id, employee_user_id, assignment_id, employee_email,
                client_id, site_id, client_id_snapshot, site_id_snapshot, branch_id,
                leave_type, date_from, date_to, reason, status, created_at
            ) VALUES (1, 1, 1, 'employee@test.local', 1, 1, 1, 1, 1,
                'izin', '2026-01-18', '2026-01-18', 'Family', 'approved',
                '2026-01-17 12:00:00')
            """
        )
        conn.commit()
    finally:
        conn.close()
    presensi._set_global_addons([presensi.ADDON_REPORTING_ADVANCED])

    flask_app = presensi.create_app()
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {
                "id": 0,
                "email": "admin@test.local",
                "role": "hr_superadmin",
                "name": "Admin",
                "tier": "pro",
            }
        query = "start_date=2026-01-16&end_date=2026-01-18&client_id=1"
        summary = client.get(f"/api/report/attendance/summary?{query}")
        assert summary.status_code == 200
        assert summary.get_json()["data"]["late_count"] == 1

        by_employee = client.get(f"/api/report/attendance/by-employee?{query}")
        assert by_employee.status_code == 200
        employee_rows = by_employee.get_json()["data"]
        assert employee_rows[0]["late_count"] == 1

        leave_pattern = client.get(f"/api/report/leave/pattern?{query}")
        assert leave_pattern.status_code == 200
        assert leave_pattern.get_json()["data"]["by_type"] == [{"total": 1, "type": "izin"}]

        geo_anomaly = client.get(f"/api/report/geo/anomaly?{query}")
        assert geo_anomaly.status_code == 200
        assert geo_anomaly.get_json()["data"][0]["reason"] == "outside_radius"


def test_approved_payroll_is_immutable_for_regenerate_and_adjustment(payroll_db, monkeypatch):
    monkeypatch.setenv("FLASK_SECRET", "test-secret-for-payroll-immutable")
    _seed_employee_policy(
        payroll_db,
        schedule=presensi.PAYROLL_SCHEDULE_MID_MONTH,
        scheme=presensi.PAYROLL_SCHEME_PRORATED,
    )
    conn = sqlite3.connect(payroll_db)
    try:
        conn.execute("UPDATE clients SET addons = ? WHERE id = 1", ('["payroll_plus"]',))
        conn.commit()
    finally:
        conn.close()
    _insert_checkins(payroll_db, ["2026-01-16"])
    payroll_id = presensi._create_payroll_record("employee@test.local", "2026-02", 3100)
    presensi._approve_payroll_record(
        payroll_id,
        presensi.User(id=99, email="admin@test.local", role="hr_superadmin", tier="pro"),
    )

    with pytest.raises(ValueError, match="approved"):
        presensi._create_payroll_record("employee@test.local", "2026-02", 9999)

    flask_app = presensi.create_app()
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as client:
        with client.session_transaction() as sess:
            sess["csrf_token"] = "csrf-test-token"
            sess["user"] = {
                "id": 0,
                "email": "client@test.local",
                "role": "client_admin",
                "name": "Client Admin",
                "tier": "pro",
                "client_id": 1,
                "site_id": 1,
            }

        response = client.post(
            f"/api/payroll/{payroll_id}/update",
            json={"potongan_lain": 10, "tunjangan": 0},
            headers={"X-CSRF-Token": "csrf-test-token"},
        )
        assert response.status_code == 400
        assert "approved" in response.get_json()["message"].lower()


def test_client_admin_cannot_access_other_client_payroll(payroll_db, monkeypatch):
    monkeypatch.setenv("FLASK_SECRET", "test-secret-for-payroll-scope")
    _seed_employee_policy(
        payroll_db,
        schedule=presensi.PAYROLL_SCHEDULE_MID_MONTH,
        scheme=presensi.PAYROLL_SCHEME_PRORATED,
    )
    _seed_other_client_employee(payroll_db)
    payroll_id = presensi._create_payroll_record("employee3@test.local", "2026-02", 3100)

    flask_app = presensi.create_app()
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {
                "id": 0,
                "email": "client@test.local",
                "role": "client_admin",
                "name": "Client Admin",
                "tier": "pro",
                "client_id": 1,
                "site_id": 1,
            }

        detail = client.get(f"/api/payroll/{payroll_id}")
        assert detail.status_code == 403

        listing = client.get("/api/payroll/list?period=2026-02")
        assert listing.status_code == 200
        payload = listing.get_json()
        assert {row["employee_email"] for row in payload["data"]} == set()


def test_admin_can_filter_payroll_by_client(payroll_db, monkeypatch):
    monkeypatch.setenv("FLASK_SECRET", "test-secret-for-admin-client-filter")
    _seed_employee_policy(
        payroll_db,
        schedule=presensi.PAYROLL_SCHEDULE_MID_MONTH,
        scheme=presensi.PAYROLL_SCHEME_PRORATED,
    )
    _seed_other_client_employee(payroll_db)
    presensi._create_payroll_record("employee@test.local", "2026-02", 3100)
    presensi._create_payroll_record("employee3@test.local", "2026-02", 3100)

    flask_app = presensi.create_app()
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {
                "id": 0,
                "email": "admin@test.local",
                "role": "hr_superadmin",
                "name": "Admin",
                "tier": "pro",
            }

        response = client.get("/api/payroll/list?period=2026-02&client_id=2")
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["ok"] is True
        assert [row["employee_email"] for row in payload["data"]] == ["employee3@test.local"]
