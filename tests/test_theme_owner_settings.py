import sys
from pathlib import Path
import sqlite3

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as presensi


@pytest.fixture()
def theme_db(tmp_path, monkeypatch):
    db_path = tmp_path / "theme.db"
    monkeypatch.setattr(presensi, "DB_PATH", str(db_path))
    presensi._init_db()
    return db_path


def test_disabled_extra_theme_falls_back_to_dark(theme_db):
    presensi._set_extra_themes_enabled(False)

    assert presensi._enabled_theme_options() == ["dark", "light"]
    assert presensi._normalize_enabled_theme("silver_line") == "dark"
    assert presensi._normalize_enabled_theme("light") == "light"


def test_extra_theme_toggle_enables_all_or_none(theme_db):
    presensi._set_extra_themes_enabled(True)
    assert presensi._enabled_extra_themes() == ["sage_calm", "silver_line", "noir_warm"]

    presensi._set_extra_themes_enabled(False)
    assert presensi._enabled_extra_themes() == []


def test_disabling_extra_themes_clears_saved_extra_preferences(theme_db):
    conn = sqlite3.connect(theme_db)
    try:
        conn.execute(
            """
            INSERT INTO users (
                id, email, name, role, password_hash, is_active,
                tier, theme_preference, created_at
            ) VALUES (1, 'admin@test.local', 'Admin', 'hr_superadmin',
                'hash', 1, 'pro', 'silver_line', '2026-01-01 00:00:00')
            """
        )
        conn.execute(
            """
            INSERT INTO clients (
                id, name, address, office_email, office_phone,
                pic_name, pic_title, pic_phone, client_theme, created_at
            ) VALUES (1, 'Client', 'Jakarta', 'hr@client.test', '021',
                'PIC', 'HR', '0812', 'noir_warm', '2026-01-01 00:00:00')
            """
        )
        conn.commit()
    finally:
        conn.close()

    presensi._set_extra_themes_enabled(False)

    conn = sqlite3.connect(theme_db)
    try:
        user_theme = conn.execute("SELECT theme_preference FROM users WHERE id = 1").fetchone()[0]
        client_theme = conn.execute("SELECT client_theme FROM clients WHERE id = 1").fetchone()[0]
    finally:
        conn.close()

    assert user_theme == "dark"
    assert client_theme == "dark"


def test_admin_theme_tab_hidden_when_extra_themes_disabled(theme_db, monkeypatch):
    monkeypatch.setenv("FLASK_SECRET", "test-secret-for-theme-tab")
    presensi._set_extra_themes_enabled(False)

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

        response = client.get("/dashboard/admin/settings?tab=theme")
        assert response.status_code == 200
        html = response.get_data(as_text=True)

    assert "tab=theme" not in html
    assert "name=\"theme_preference\"" not in html


def test_owner_suite_modes_control_global_addons_and_brand(theme_db):
    presensi._set_global_addons([presensi.ADDON_HRIS_PRO])
    assert presensi._owner_suite_mode() == presensi.OWNER_SUITE_PRO
    assert presensi._hris_brand_title() == "HRIS PRO"
    assert presensi._global_addons() == [presensi.ADDON_HRIS_PRO]

    presensi._set_global_addons([presensi.ADDON_HRIS_PRO_PLUS, presensi.ADDON_PATROL, presensi.ADDON_BILLING_ENGINE])
    pro_plus_addons = set(presensi._global_addons())
    assert presensi._owner_suite_mode() == presensi.OWNER_SUITE_PRO_PLUS
    assert presensi._hris_brand_title() == "HRIS PRO PLUS"
    assert presensi.ADDON_PATROL in pro_plus_addons
    assert presensi.ADDON_BILLING_ENGINE in pro_plus_addons
    assert presensi.ADDON_CONTRACT_MANAGEMENT in pro_plus_addons

    presensi._set_global_addons([presensi.ADDON_ENTERPRISE_TIER])
    enterprise_addons = set(presensi._global_addons())
    assert presensi._owner_suite_mode() == presensi.OWNER_SUITE_ENTERPRISE
    assert presensi._hris_brand_title() == "HRIS ENTERPRISE"
    assert presensi.ADDON_API_ACCESS in enterprise_addons
    assert presensi.ADDON_REPORTING_ADVANCED in enterprise_addons


def test_admin_employee_page_hides_addon_nav_when_owner_mode_is_hris_pro(theme_db, monkeypatch):
    monkeypatch.setenv("FLASK_SECRET", "test-secret-for-employee-nav")
    presensi._set_global_addons([presensi.ADDON_HRIS_PRO])

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

        response = client.get("/dashboard/admin/employees")
        assert response.status_code == 200
        html = response.get_data(as_text=True)

    assert 'href="/dashboard/admin/calendar"' not in html
    assert 'href="/dashboard/admin/ai-analysis"' not in html
    assert 'href="/dashboard/admin/billing"' not in html
    assert 'href="/dashboard/admin/contract"' not in html
