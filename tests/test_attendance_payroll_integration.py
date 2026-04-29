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
    assert detail["payroll_scheme"] == presensi.PAYROLL_SCHEME_PRORATED
    assert detail["calculation_version"] == presensi.PAYROLL_CALCULATION_VERSION
    assert rows[0]["total_gaji"] == detail["total_gaji"]


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
