import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as presensi


@pytest.fixture()
def phase15_db(tmp_path, monkeypatch):
    db_path = tmp_path / "phase15.db"
    monkeypatch.setattr(presensi, "DB_PATH", str(db_path))
    presensi._init_db()
    return db_path


def _seed_client_usage(db_path: Path) -> int:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO clients (
                id, name, address, office_email, office_phone,
                pic_name, pic_title, pic_phone, created_at
            ) VALUES (1, 'Acme', 'Jakarta', 'finance@acme.test', '021',
                'PIC', 'Finance', '0812', '2026-01-01 00:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO sites (id, client_id, name, is_active, created_at)
            VALUES (1, 1, 'Site A', 1, '2026-01-01 00:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO assignments (
                employee_user_id, client_id, site_id, start_date, status, created_at
            ) VALUES (100, 1, 1, '2026-04-01', 'ACTIVE', '2026-04-01 00:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO attendance (
                employee_id, client_id, branch_id, employee_name, employee_email,
                date, time, action, method, created_at
            ) VALUES (100, 1, 1, 'Employee', 'emp@acme.test',
                '2026-04-10', '08:00', 'checkin', 'qr', '2026-04-10 08:00:00')
            """
        )
        conn.commit()
    finally:
        conn.close()
    return 1


def test_billing_summary_stays_zero_until_enterprise_billing_enabled(phase15_db):
    client_id = _seed_client_usage(phase15_db)
    presensi._save_client_contract(client_id, "CTR-001", "2026-04-01", "2027-03-31", 30, "Scope", "SLA")
    presensi._save_billing_config(client_id, "PER_HEAD", 100000, 10, 14, "finance@acme.test")

    summary = presensi._client_billing_summary(client_id, "2026-04")

    assert summary["billing_enabled"] is False
    assert summary["calculated_amount"] == 0
    assert summary["total_employees"] == 1
    assert any("Billing belum aktif" in warning for warning in summary["warnings"])


def test_enterprise_billing_summary_calculates_per_head_with_tax(phase15_db):
    client_id = _seed_client_usage(phase15_db)
    presensi._set_client_package(client_id, "ENTERPRISE")
    presensi._set_client_addons(client_id, ["BILLING_ENGINE", "CONTRACT_MANAGEMENT"])
    presensi._save_client_contract(client_id, "CTR-002", "2026-04-01", "2027-03-31", 30, "Scope", "SLA")
    presensi._save_billing_config(client_id, "PER_HEAD", 100000, 10, 14, "finance@acme.test")

    summary = presensi._client_billing_summary(client_id, "2026-04")

    assert summary["billing_enabled"] is True
    assert summary["billing_type"] == "PER_HEAD"
    assert summary["unit_count"] == 1
    assert summary["subtotal"] == 100000
    assert summary["tax_amount"] == 10000
    assert summary["calculated_amount"] == 110000
    assert summary["warnings"] == []


def test_api_access_client_addon_persists_to_primary_and_legacy_storage(phase15_db):
    client_id = _seed_client_usage(phase15_db)
    presensi._set_global_addons([presensi.ADDON_API_ACCESS])

    active = presensi._set_client_addons(client_id, [presensi.ADDON_API_ACCESS])

    assert active == [presensi.ADDON_API_ACCESS]
    assert presensi._list_client_addons(client_id) == [presensi.ADDON_API_ACCESS]

    conn = sqlite3.connect(phase15_db)
    conn.row_factory = sqlite3.Row
    try:
        addon_row = conn.execute(
            """
            SELECT is_enabled FROM client_addons
            WHERE client_id = ? AND addon_key = ?
            """,
            (client_id, presensi.ADDON_API_ACCESS),
        ).fetchone()
        client_row = conn.execute("SELECT addons FROM clients WHERE id = ?", (client_id,)).fetchone()
    finally:
        conn.close()

    assert addon_row["is_enabled"] == 1
    assert presensi.ADDON_API_ACCESS in presensi._addons_from_value(client_row["addons"])
    assert presensi.has_addon(presensi._get_client_by_id(client_id), presensi.ADDON_API_ACCESS) is True


def test_api_access_legacy_client_addons_are_used_as_fallback(phase15_db):
    client_id = _seed_client_usage(phase15_db)
    presensi._set_global_addons([presensi.ADDON_API_ACCESS])
    conn = sqlite3.connect(phase15_db)
    try:
        conn.execute(
            "UPDATE clients SET addons = ? WHERE id = ?",
            (presensi._addons_json([presensi.ADDON_API_ACCESS]), client_id),
        )
        conn.commit()
    finally:
        conn.close()

    assert presensi._list_client_addons(client_id) == [presensi.ADDON_API_ACCESS]
    assert presensi.has_addon(presensi._get_client_by_id(client_id), presensi.ADDON_API_ACCESS) is True


def test_client_addons_source_of_truth_wins_over_stale_legacy_addons(phase15_db):
    client_id = _seed_client_usage(phase15_db)
    presensi._set_global_addons([presensi.ADDON_API_ACCESS])
    now = presensi._now_ts()
    conn = sqlite3.connect(phase15_db)
    try:
        conn.execute(
            "UPDATE clients SET addons = ? WHERE id = ?",
            (presensi._addons_json([presensi.ADDON_API_ACCESS]), client_id),
        )
        conn.execute(
            """
            INSERT INTO client_addons (client_id, addon_key, is_enabled, created_at, updated_at)
            VALUES (?, ?, 0, ?, ?)
            """,
            (client_id, presensi.ADDON_API_ACCESS, now, now),
        )
        conn.commit()
    finally:
        conn.close()

    assert presensi._list_client_addons(client_id) == []
    assert presensi.has_addon(presensi._get_client_by_id(client_id), presensi.ADDON_API_ACCESS) is False

    presensi._init_db()

    assert presensi._list_client_addons(client_id) == []
    assert presensi.has_addon(presensi._get_client_by_id(client_id), presensi.ADDON_API_ACCESS) is False


def test_client_feature_enabled_respects_api_access_addon(phase15_db):
    client_id = _seed_client_usage(phase15_db)
    presensi._set_global_addons([presensi.ADDON_API_ACCESS])
    presensi._set_client_addons(client_id, [presensi.ADDON_API_ACCESS])
    user = presensi.User(id=10, email="client@acme.test", role="client_admin", client_id=client_id)

    assert presensi._client_feature_enabled(user, presensi.ADDON_API_ACCESS, client_id) is True
