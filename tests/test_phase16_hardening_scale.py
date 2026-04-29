import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as presensi


@pytest.fixture()
def phase16_db(tmp_path, monkeypatch):
    db_path = tmp_path / "phase16.db"
    monkeypatch.setattr(presensi, "DB_PATH", str(db_path))
    presensi._init_db()
    return db_path


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def test_phase16_hardening_schema_and_seed_data_created(phase16_db):
    conn = sqlite3.connect(phase16_db)
    try:
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        }
        assert {"roles", "permissions", "role_permission_map", "user_scopes", "retention_policies", "login_attempts"} <= tables

        assert {"deleted_at", "deleted_by", "delete_reason"} <= _columns(conn, "clients")
        assert {"deleted_at", "deleted_by", "delete_reason"} <= _columns(conn, "sites")
        assert {"created_by_user_id", "updated_by_user_id", "updated_at"} <= _columns(conn, "billing_configs")
        assert {"before_json", "after_json", "ip_address", "user_agent"} <= _columns(conn, "audit_logs")

        permissions = {
            row[0] for row in conn.execute("SELECT permission_key FROM permissions").fetchall()
        }
        assert {"billing.view", "billing.config.update", "contract.manage", "audit.view"} <= permissions

        retention = {
            row[0]: row[1]
            for row in conn.execute("SELECT data_type, retention_days FROM retention_policies").fetchall()
        }
        assert retention["attendance"] == 1825
        assert retention["temporary_uploads"] == 90
    finally:
        conn.close()


def test_phase16_required_indexes_created(phase16_db):
    conn = sqlite3.connect(phase16_db)
    try:
        indexes = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'index'").fetchall()
        }
        assert "idx_attendance_client_date" in indexes
        assert "idx_employees_client_site" in indexes
        assert "idx_leave_client_status" in indexes
        assert "idx_audit_client_created" in indexes
        assert "idx_billing_client_active" in indexes
    finally:
        conn.close()


def test_login_rate_limit_uses_persistent_attempts_table(phase16_db):
    identifier = "admin@test.local"
    ip_address = "127.0.0.1"

    for _ in range(presensi.LOGIN_RATE_LIMIT_MAX):
        presensi._record_login_attempt(identifier, ip_address, False)

    assert presensi._login_rate_limited(identifier, ip_address) is True
    assert presensi._login_rate_limited("other@test.local", ip_address) is False
