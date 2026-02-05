from __future__ import annotations

import base64
import calendar
import csv
import io
import json
import re
import os
import math
import sqlite3
import secrets
import hashlib
import hmac
import time
import logging
from datetime import datetime, date, timedelta, timezone
from dataclasses import dataclass
from typing import Dict

import qrcode

from flask import Flask, jsonify, render_template, request, session, Blueprint, abort, redirect, url_for, flash, g
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash


@dataclass
class AuthResult:
    ok: bool
    message: str
    next_url: str | None = None


APP_BOOT_ID = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
PERF_LOG = (os.environ.get("PERF_LOG") or "").lower() in {"1", "true", "yes"}
PERF_LOGGER = logging.getLogger("perf")
try:
    ADMIN_LIST_LIMIT = int(os.environ.get("ADMIN_LIST_LIMIT") or 0)
except ValueError:
    ADMIN_LIST_LIMIT = 0
try:
    PENDING_LIST_LIMIT = int(os.environ.get("PENDING_LIST_LIMIT") or 0)
except ValueError:
    PENDING_LIST_LIMIT = 0


def _perf_log(label: str, start_time: float, extra: str = "") -> None:
    if not PERF_LOG:
        return
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    suffix = f" | {extra}" if extra else ""
    PERF_LOGGER.info("PERF %s %.1fms%s", label, elapsed_ms, suffix)


def create_app() -> Flask:
    app = Flask(__name__)
    secret = os.environ.get("FLASK_SECRET")
    if not secret:
        secret = "presensi-default-secret"
    app.secret_key = secret
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "").lower() in {"1", "true", "yes"},
        MAX_CONTENT_LENGTH=12 * 1024 * 1024,
    )

    @app.after_request
    def _security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Permissions-Policy",
            "geolocation=(self), camera=(self), microphone=()",
        )
        return response

    @app.context_processor
    def _inject_boot_id():
        return {"boot_id": APP_BOOT_ID}

    @app.before_request
    def _enforce_active_user():
        if not session.get("user"):
            return None
        user = _current_user()
        if user:
            return None
        session.clear()
        if request.path.startswith("/api/"):
            return jsonify(ok=False, message="Session sudah berakhir."), 401
        return redirect(url_for("index"))

    @app.before_request
    def _perf_request_start():
        if PERF_LOG:
            g._perf_start = time.perf_counter()

    @app.after_request
    def _perf_request_end(response):
        if PERF_LOG:
            start = getattr(g, "_perf_start", None)
            if start is not None:
                elapsed_ms = (time.perf_counter() - start) * 1000
                PERF_LOGGER.info(
                    "REQ %s %s %s %.1fms",
                    request.method,
                    request.path,
                    response.status_code,
                    elapsed_ms,
                )
        return response

    def _ensure_csrf_token() -> str:
        token = session.get("csrf_token")
        if not token:
            token = secrets.token_urlsafe(32)
            session["csrf_token"] = token
        return token

    @app.before_request
    def _csrf_guard():
        if request.method not in {"POST", "PUT", "DELETE"}:
            return None
        if request.path in {"/api/auth/login", "/api/auth/forgot", "/api/auth/reset"}:
            return None
        if not session.get("user"):
            return None
        content_type = request.content_type or ""
        token = session.get("csrf_token")
        if content_type.startswith("application/json"):
            header_token = (request.headers.get("X-CSRF-Token") or request.headers.get("X-CSRFToken") or "").strip()
            body = request.get_json(silent=True) or {}
            body_token = (body.get("csrf_token") or "").strip() if isinstance(body, dict) else ""
            req_token = header_token or body_token
        else:
            req_token = (request.form.get("csrf_token") or "").strip()
        
        if not token or req_token != token:
            if request.path == "/api/attendance/checkin":
                print(f"[CSRF_ERROR] Token mismatch - aborting 403")
            return abort(403)
        return None

    @app.context_processor
    def _inject_csrf_token():
        return {"csrf_token": _ensure_csrf_token()}

    @app.context_processor
    def _inject_permissions():
        user = _current_user()
        if not user:
            return {"permissions": {}}
        return {"permissions": _get_role_permissions(user.role)}

    @app.context_processor
    def _inject_notifications():
        user = _current_user()
        if not user:
            return {"pending_leave_count": 0, "pending_manual_count": 0}
        pending_leave_count = 0
        pending_manual_count = 0
        if _can_approve_leave(user):
            pending_leave_count = len(_list_leave_pending(user))
        if _can_approve_manual(user):
            pending_manual_count = len(_fetch_manual_requests("pending", user))
        return {
            "pending_leave_count": pending_leave_count,
            "pending_manual_count": pending_manual_count,
        }

    def _parse_display_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        raw = str(value).strip()
        if not raw:
            return None
        candidate = raw
        if candidate.endswith("Z"):
            candidate = candidate[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(candidate)
        except ValueError:
            pass
        for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y", "%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M", "%d-%m-%Y"):
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                continue
        return None

    def _format_display_date(value: str | None) -> str:
        dt = _parse_display_datetime(value)
        if dt:
            return dt.strftime("%d-%m-%Y")
        if value:
            return str(value).strip()
        return "-"

    @app.template_filter("ddmmyyyy")
    def _format_ddmmyyyy(value: str | None) -> str:
        dt = _parse_display_datetime(value)
        if dt:
            return dt.strftime("%d-%m-%Y")
        if value:
            return str(value).strip()
        return ""

    @app.template_filter("display_datetime")
    def _format_display_datetime(value: str | None) -> str:
        dt = _parse_display_datetime(value)
        if dt:
            return dt.strftime("%d-%m-%Y %H:%M")
        if value:
            return str(value).strip()
        return ""

    app.register_blueprint(admin_bp())
    _init_db()

    @app.route("/api/auth/login", methods=["POST"])
    def login():
        data = _get_json()
        result = _validate_login(data)
        if result.ok:
            user = _current_user()
            _log_audit_event(
                entity_type="auth",
                entity_id=user.id if user else None,
                action="LOGIN",
                actor=user,
                summary="Login berhasil.",
                details={"email": user.email if user else None, "role": user.role if user else None},
            )
        status = 200 if result.ok else 400
        return jsonify(result.__dict__), status

    @app.route("/api/auth/signup", methods=["POST"])
    def signup():
        data = request.form or {}
        invite = (data.get("invite_code") or "").strip()
        login_type = (data.get("login_type") or "email").strip().lower()
        identifier = (data.get("identifier") or data.get("email") or data.get("phone") or "").strip()
        email = ""
        p1 = data.get("password", "")
        p2 = data.get("password2", "")
        selfie_file = request.files.get("selfie")

        if not invite:
            return jsonify(ok=False, message="Kode undangan wajib."), 400
        if login_type == "phone":
            phone = _normalize_phone(identifier)
            if not phone:
                return jsonify(ok=False, message="No telp wajib diisi."), 400
            employee = _employee_by_phone(phone, only_active=False)
            if not employee:
                return jsonify(ok=False, message="No telp tidak ditemukan."), 400
            email = (employee.get("email") or "").strip()
            if not email:
                return jsonify(ok=False, message="Email akun tidak ditemukan."), 400
        else:
            email = identifier
            if not _looks_like_email(email):
                return jsonify(ok=False, message="Email tidak valid."), 400
        if len(p1) < 6:
            return jsonify(ok=False, message="Password minimal 6 karakter."), 400
        if p1 != p2:
            return jsonify(ok=False, message="Password tidak sama."), 400
        if not selfie_file or not selfie_file.filename:
            return jsonify(ok=False, message="Selfie wajib untuk daftar."), 400

        invite = invite.strip().upper()
        normalized_invite = invite.replace(" ", "")
        is_manual_code = normalized_invite == "SUDAHBYADMIN"
        if is_manual_code:
            if not _employee_by_email(email, only_active=False):
                return jsonify(
                    ok=False,
                    message="Data master pegawai belum ada. Hubungi admin untuk input data.",
                ), 400
        else:
            if not _looks_like_employee_invite(invite):
                return jsonify(ok=False, message="Format kode undangan tidak valid."), 400
            if _employee_by_email(email, only_active=False):
                return jsonify(
                    ok=False,
                    message="Data master pegawai sudah ada. Gunakan kode SUDAHBYADMIN.",
                ), 400

        if _get_user_by_email(email):
            return jsonify(ok=False, message="Email sudah terdaftar."), 400

        try:
            _validate_upload(selfie_file, 10 * 1024 * 1024)
        except ValueError as err:
            return jsonify(ok=False, message=str(err)), 400

        conn = _db_connect()
        selfie_path = None
        committed = False
        try:
            conn.execute("BEGIN IMMEDIATE")
            existing = conn.execute(
                "SELECT 1 FROM users WHERE email = ?",
                (email.lower(),),
            ).fetchone()
            if existing:
                conn.rollback()
                return jsonify(ok=False, message="Email sudah terdaftar."), 400
            if not is_manual_code:
                ok, message = _consume_employee_registration_code_with_conn(conn, invite)
                if not ok:
                    conn.rollback()
                    return jsonify(ok=False, message=message), 400

            user_id = _create_user_with_conn(
                conn,
                name=email.split("@")[0],
                email=email,
                role="employee",
                password=p1,
                selfie_path=None,
            )
            try:
                selfie_path = _save_upload(selfie_file, "uploads/selfies", 10 * 1024 * 1024)
            except ValueError as err:
                conn.rollback()
                return jsonify(ok=False, message=str(err)), 400
            except Exception:
                conn.rollback()
                return jsonify(ok=False, message="Gagal menyimpan file selfie."), 400
            _update_user_selfie_path_with_conn(conn, user_id, selfie_path)
            if is_manual_code:
                _set_employee_active_with_conn(conn, email, 1)
            conn.commit()
            committed = True
        finally:
            conn.close()
            if not committed and selfie_path:
                _delete_uploaded_file(selfie_path)
        return jsonify(ok=True, message="Signup berhasil (demo)."), 200

    @app.route("/api/auth/forgot", methods=["POST"])
    def forgot():
        data = _get_json()
        login_type = (data.get("login_type") or "email").strip().lower()
        method = (data.get("method") or "email_link").strip().lower()
        identifier = (data.get("identifier") or data.get("email") or data.get("phone") or "").strip()
        email = ""

        if method not in {"email_link", "whatsapp_otp"}:
            return jsonify(ok=False, message="Metode reset tidak dikenali."), 400

        if login_type == "phone":
            phone = _normalize_phone(identifier)
            if not phone:
                return jsonify(ok=False, message="No telp wajib diisi."), 400
            employee = _employee_by_phone(phone, only_active=False)
            if not employee:
                return jsonify(ok=False, message="No telp tidak ditemukan."), 400
            email = (employee.get("email") or "").strip()
            if not email:
                return jsonify(ok=False, message="Email akun tidak ditemukan."), 400
        else:
            email = identifier
            if not _looks_like_email(email):
                return jsonify(ok=False, message="Email wajib diisi."), 400
        token = None
        row = _get_user_by_email(email)
        if row and int(_row_get(row, "is_active") or 0) == 1:
            if method == "whatsapp_otp":
                token = _create_password_reset_token(int(row["id"]), _generate_otp_token(), ttl_minutes=10)
            else:
                token = _create_password_reset_token(int(row["id"]))
        response = {"ok": True, "message": "Jika akun terdaftar, instruksi reset telah dikirim."}
        if token and (os.environ.get("SHOW_RESET_TOKEN") or "").lower() in {"1", "true", "yes"}:
            response["reset_token"] = token
        return jsonify(response), 200

    @app.route("/api/auth/reset_password", methods=["POST"])
    def reset_password():
        data = _get_json()
        token = (data.get("token") or "").strip()
        new_password = data.get("new_password", "")
        new_password2 = data.get("new_password2", "")
        if not token:
            return jsonify(ok=False, message="Token reset wajib diisi."), 400
        if len(new_password) < 6:
            return jsonify(ok=False, message="Password baru minimal 6 karakter."), 400
        if new_password != new_password2:
            return jsonify(ok=False, message="Password baru tidak sama."), 400
        user_id = _consume_password_reset_token(token)
        if not user_id:
            return jsonify(ok=False, message="Token reset tidak valid atau kadaluarsa."), 400
        _update_user_password(user_id, new_password, 0)
        user_row = _get_user_by_id(user_id)
        actor = _user_row_to_user(user_row, "dark") if user_row else None
        _log_audit_event(
            entity_type="auth",
            entity_id=user_id,
            action="RESET_PASSWORD",
            actor=actor,
            summary="Password direset menggunakan token.",
        )
        return jsonify(ok=True, message="Password berhasil diperbarui."), 200

    @app.route("/api/auth/change_password", methods=["POST"])
    def change_password():
        user = _current_user()
        if not user:
            return _json_forbidden()
        data = _get_json()
        current_password = data.get("current_password", "")
        new_password = data.get("new_password", "")
        new_password2 = data.get("new_password2", "")

        if len(new_password) < 6:
            return jsonify(ok=False, message="Password baru minimal 6 karakter."), 400
        if new_password != new_password2:
            return jsonify(ok=False, message="Password baru tidak sama."), 400
        row = _get_user_by_id(user.id)
        if not row:
            return jsonify(ok=False, message="Akun tidak ditemukan."), 404
        if not check_password_hash(row["password_hash"], current_password):
            return jsonify(ok=False, message="Password saat ini salah."), 400

        _update_user_password(user.id, new_password, 0)
        user.must_change_password = 0
        _persist_user(user)
        _log_audit_event(
            entity_type="auth",
            entity_id=user.id,
            action="CHANGE_PASSWORD",
            actor=user,
            summary="Password diubah.",
        )
        return jsonify(ok=True, message="Password berhasil diperbarui."), 200

    @app.route("/api/user/profile_photo", methods=["POST"])
    def update_profile_photo():
        user = _current_user()
        if not user:
            return _json_forbidden()
        avatar_file = request.files.get("avatar")
        if not avatar_file or not avatar_file.filename:
            return jsonify(ok=False, message="Foto profil wajib diunggah."), 400
        try:
            selfie_path = _save_upload(avatar_file, "uploads/profiles", 10 * 1024 * 1024)
        except ValueError as err:
            return jsonify(ok=False, message=str(err)), 400

        _update_user_selfie_path(user.id, selfie_path)
        user.selfie_path = selfie_path
        _persist_user(user)
        return jsonify(ok=True, message="Foto profil diperbarui.", path=url_for("static", filename=selfie_path)), 200

    @app.route("/api/employee/profile", methods=["POST"])
    def employee_profile_create():
        user = _current_user()
        forbidden = _require_api_role(user, EMPLOYEE_ROLES)
        if forbidden:
            return forbidden
        payload, error = _parse_employee_form(request.form or {})
        if error:
            return jsonify(ok=False, message=error), 400
        if user.email.lower() != payload["email"].lower():
            return jsonify(ok=False, message="Email tidak sesuai akun."), 400
        if _employee_by_email(user.email, only_active=False):
            return jsonify(ok=False, message="Data master pegawai sudah terdaftar."), 400
        conflict = _employee_conflict(payload["email"], payload["nik"], payload["no_hp"])
        if conflict:
            return jsonify(ok=False, message=conflict), 400
        _create_employee(**payload)
        return jsonify(ok=True, message="Data pegawai berhasil disimpan."), 200

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify(status="ok"), 200

    @app.route("/", methods=["GET"])
    def index():
        return render_template("index.html", theme="dark")

    @app.route("/dashboard/pegawai", methods=["GET"])
    def dashboard_employee():
        user = _current_user()
        _require_role(user, EMPLOYEE_ROLES)
        employee = _employee_by_email(user.email, only_active=False)
        has_employee_record = bool(employee)
        assignment = _get_active_assignment(user.id) if user else None
        site = _get_site_by_id(assignment.get("site_id") if assignment else None)
        client = _get_client_by_id(site["client_id"]) if site and site["client_id"] else None
        shift = _get_shift_by_id(assignment.get("shift_id") if assignment else None)
        return render_template(
            "dashboard/employee.html",
            user=user,
            employee=employee,
            has_employee_record=has_employee_record,
            active_assignment=assignment,
            active_site=site,
            active_client=client,
            active_shift=shift,
        )

    @app.route("/dashboard/client", methods=["GET"])
    def dashboard_client():
        user = _current_user()
        _require_client_user(user)
        client_id, site_id, site, client = _client_site_context(user)
        today = _today_key()
        employees = _list_employees_by_site(site_id)
        employee_emails = {
            (row.get("email") or "").lower()
            for row in employees
            if row.get("email")
        }
        active_employees = [
            row
            for row in employees
            if str(row.get("is_active", 1)).strip().lower() not in {"0", "false"}
        ]
        email_to_user_id = {
            (row.get("email") or "").lower(): int(row["id"])
            for row in employees
            if row.get("email") and row.get("id")
        }
        checkins = _attendance_checkins_for_date(today, email_to_user_id)
        checked_in_ids = {int(user_id) for user_id in checkins.keys() if user_id}
        leave_status_map = _leave_status_by_email_for_date(today, employee_emails)
        absent_employees = []
        for row in active_employees:
            user_id = row.get("id")
            if user_id and int(user_id) in checked_in_ids:
                continue
            email = (row.get("email") or "").lower()
            leave_info = leave_status_map.get(email)
            if leave_info and leave_info.get("status") == "pending":
                note = "Approval pending"
            elif leave_info and leave_info.get("status") == "approved":
                leave_type = leave_info.get("type")
                if leave_type == "izin":
                    note = "izin"
                elif leave_type == "sakit":
                    note = "sakit"
                else:
                    note = "tidak ada info"
            else:
                note = "tidak ada info"
            absent_employees.append(
                {
                    "employee": row.get("name") or row.get("email") or "-",
                    "note": note,
                }
            )
        present_today = _attendance_today_count_for_emails(today, employee_emails)
        site_summary = _site_operational_summary(today, site_id)
        leave_breakdown = _client_leave_breakdown(today, employee_emails)
        leave_pending = _leave_pending_count_for_emails(employee_emails)
        attendance_records = _attendance_live(limit=20, allowed_emails=employee_emails)
        policies = _policies_for_site(client_id, site_id)
        client_users = _client_users_for_site(client_id, site_id)
        return render_template(
            "dashboard/client.html",
            user=user,
            client=client,
            site=site,
            today=today,
            employees=employees,
            attendance_records=attendance_records,
            absent_employees=absent_employees,
            policies=policies,
            client_users=client_users,
            total_employees=len(employees),
            present_today=present_today,
            late_today=int(site_summary.get("late_count") or 0),
            absent_today=int(site_summary.get("absent_count") or 0),
            leave_pending=int(leave_pending or 0),
            leave_sakit=int(leave_breakdown.get("sakit") or 0),
            leave_izin=int(leave_breakdown.get("izin") or 0),
            can_manage_site=user.role == "client_admin",
            can_manage_employees=user.role == "client_admin",
            can_manage_policies=user.role == "client_admin",
            can_manage_users=user.role == "client_admin",
            can_change_password=user.role == "client_admin",
        )

    @app.route("/client/site/update", methods=["POST"])
    def client_site_update():
        user = _current_user()
        _require_client_admin(user)
        client_id, site_id, site, _client = _client_site_context(user)
        name = (request.form.get("name") or "").strip()
        timezone = (request.form.get("timezone") or "").strip()
        work_mode = (request.form.get("work_mode") or "").strip().upper()
        latitude_raw = (request.form.get("latitude") or "").strip()
        longitude_raw = (request.form.get("longitude") or "").strip()
        radius_raw = (request.form.get("radius_meters") or "").strip()
        notes = (request.form.get("notes") or "").strip()
        if not name:
            flash("Nama site wajib diisi.")
            return redirect(url_for("dashboard_client", _anchor="site"))
        try:
            latitude = float(latitude_raw)
            longitude = float(longitude_raw)
            radius_meters = int(radius_raw)
        except ValueError:
            flash("Latitude, longitude, dan radius wajib angka.")
            return redirect(url_for("dashboard_client", _anchor="site"))
        if radius_meters <= 0:
            flash("Radius harus lebih besar dari 0.")
            return redirect(url_for("dashboard_client", _anchor="site"))
        _update_site(
            site_id=site_id,
            client_id=client_id,
            name=name,
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
            notes=notes,
            timezone=timezone or None,
            work_mode=work_mode or None,
        )
        flash("Site berhasil diperbarui.")
        return redirect(url_for("dashboard_client", _anchor="site"))

    @app.route("/client/employees/create", methods=["POST"])
    def client_employees_create():
        user = _current_user()
        _require_client_admin(user)
        _client_id, site_id, _site, _client = _client_site_context(user)
        payload, error = _parse_employee_form(request.form or {})
        if error:
            flash(error)
            return redirect(url_for("dashboard_client", _anchor="employees"))
        conflict = _employee_conflict(payload["email"], payload["nik"], payload["no_hp"])
        if conflict:
            flash(conflict)
            return redirect(url_for("dashboard_client", _anchor="employees"))
        assignment_payload, assignment_error = _parse_assignment_payload(request.form or {})
        if assignment_error:
            flash(assignment_error)
            return redirect(url_for("dashboard_client", _anchor="employees"))
        shift_id = assignment_payload["shift_id"]
        if shift_id:
            shift_row = _get_shift_by_id(shift_id)
            if not shift_row or int(shift_row.get("is_active") or 0) != 1:
                flash("Shift tidak ditemukan atau nonaktif.")
                return redirect(url_for("dashboard_client", _anchor="employees"))
        if int(_row_get(_site, "is_active") or 0) != 1:
            flash("Site penempatan sedang nonaktif.")
            return redirect(url_for("dashboard_client", _anchor="employees"))
        _create_employee(
            nik=payload["nik"],
            name=payload["name"],
            email=payload["email"],
            no_hp=payload["no_hp"],
            address=payload["address"],
            gender=payload["gender"],
            status_nikah=payload["status_nikah"],
            notes=payload["notes"],
            is_active=1,
            site_id=site_id,
        )
        message = "Pegawai berhasil ditambahkan."
        user_row = _get_user_by_email(payload["email"])
        if user_row:
            employee_user_id = int(_row_get(user_row, "id") or 0)
            if employee_user_id:
                try:
                    _create_assignment_with_log(
                        actor=user,
                        employee_user_id=employee_user_id,
                        site_id=site_id,
                        shift_id=shift_id,
                        job_title=assignment_payload["job_title"],
                        start_date=assignment_payload["start_date"],
                        end_date=assignment_payload["end_date"],
                        status=assignment_payload["status"],
                        summary=f"Assignment dibuat dari dashboard client untuk user_id {employee_user_id} ke site_id {site_id}.",
                        portal="client_dashboard",
                        extra_details={"source": "client_dashboard"},
                    )
                    message = "Pegawai berhasil ditambahkan dan assignment tersimpan."
                except sqlite3.Error as exc:
                    message = f"Pegawai berhasil ditambahkan. Assignment gagal: {str(exc)}"
        else:
            message = "Pegawai berhasil ditambahkan. Assignment akan aktif setelah akun pegawai tersedia."
        flash(message)
        return redirect(url_for("dashboard_client", _anchor="employees"))

    @app.route("/client/employees/<int:employee_id>/update", methods=["POST"])
    def client_employees_update(employee_id: int):
        user = _current_user()
        _require_client_admin(user)
        _client_id, site_id, _site, _client = _client_site_context(user)
        employee = _employee_by_id(employee_id)
        if not employee or int(employee.get("site_id") or 0) != site_id:
            flash("Pegawai tidak ditemukan.")
            return redirect(url_for("dashboard_client", _anchor="employees"))
        payload, error = _parse_employee_form(request.form or {})
        if error:
            flash(error)
            return redirect(url_for("dashboard_client", _anchor="employees"))
        conflict = _employee_conflict(
            payload["email"],
            payload["nik"],
            payload["no_hp"],
            exclude_id=int(employee.get("id") or 0),
        )
        if conflict:
            flash(conflict)
            return redirect(url_for("dashboard_client", _anchor="employees"))
        is_active = 1 if (request.form.get("is_active") or "0") == "1" else 0
        _update_employee(
            employee_id=int(employee.get("id") or employee_id),
            nik=payload["nik"],
            name=payload["name"],
            email=payload["email"],
            no_hp=payload["no_hp"],
            address=payload["address"],
            gender=payload["gender"],
            status_nikah=payload["status_nikah"],
            notes=payload["notes"],
            is_active=is_active,
        )
        flash("Data pegawai berhasil diperbarui.")
        return redirect(url_for("dashboard_client", _anchor="employees"))

    @app.route("/client/employees/delete", methods=["POST"])
    def client_employees_delete():
        user = _current_user()
        _require_client_admin(user)
        _client_id, site_id, _site, _client = _client_site_context(user)
        email = (request.form.get("email") or "").strip().lower()
        if not email:
            flash("Email pegawai tidak valid.")
            return redirect(url_for("dashboard_client", _anchor="employees"))
        employee = _employee_by_email(email, only_active=False)
        employee_site_id = int(employee.get("site_id") or 0) if employee else 0
        if not employee or employee_site_id != site_id:
            flash("Pegawai tidak ditemukan.")
            return redirect(url_for("dashboard_client", _anchor="employees"))
        user_row = _get_user_by_email(email)
        employee_user_id = int(_row_get(user_row, "id") or 0) if user_row else 0
        if employee_user_id:
            deleted = _delete_assignments_for_employee(employee_user_id, site_id)
        else:
            deleted = 0
        _delete_employee(int(employee["id"]))
        _log_audit_event(
            entity_type="employee",
            entity_id=int(employee.get("id") or 0),
            action="DELETE",
            actor=user,
            summary=f"Pegawai {email} dihapus dari dashboard client.",
            details={"email": email, "site_id": site_id, "assignments_deleted": deleted},
        )
        flash("Pegawai berhasil dihapus.")
        return redirect(url_for("dashboard_client", _anchor="employees"))

    @app.route("/client/attendance/csv", methods=["GET"])
    def client_attendance_csv():
        user = _current_user()
        _require_client_user(user)
        client_id, site_id, site, _client = _client_site_context(user)
        attendance_anchor = "attendance-report"
        mode = (request.args.get("mode") or "all").strip().lower()
        date_from: str | None = None
        date_to: str | None = None

        if mode == "range":
            start_raw = request.args.get("from") or ""
            end_raw = request.args.get("to") or ""
            date_from = _normalize_date_input(start_raw)
            date_to = _normalize_date_input(end_raw)
            if not date_from or not date_to:
                flash("Rentang tanggal tidak valid.")
                return redirect(url_for("dashboard_client", _anchor=attendance_anchor))
            if date_from > date_to:
                date_from, date_to = date_to, date_from
        elif mode == "month":
            month_raw = (request.args.get("month") or "").strip()
            if not month_raw:
                flash("Bulan wajib diisi untuk mode Bulan.")
                return redirect(url_for("dashboard_client", _anchor=attendance_anchor))
            try:
                month_dt = datetime.strptime(month_raw, "%m-%Y")
            except ValueError:
                flash("Format bulan harus MM-YYYY.")
                return redirect(url_for("dashboard_client", _anchor=attendance_anchor))
            date_from = month_dt.strftime("%Y-%m-01")
            last_day = calendar.monthrange(month_dt.year, month_dt.month)[1]
            date_to = datetime(month_dt.year, month_dt.month, last_day).strftime("%Y-%m-%d")
        else:
            mode = "all"

        employees = _list_employees_by_site(site_id)
        allowed_emails = {
            (row.get("email") or "").strip().lower()
            for row in employees
            if (row.get("email") or "").strip()
        }

        rows = _attendance_rows_for_emails(
            allowed_emails,
            date_from=date_from,
            date_to=date_to,
        )
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["Pegawai", "Email", "Tanggal", "Waktu", "Aksi", "Metode", "Sumber", "Dicatat"])
        for row in rows:
            writer.writerow(
                [
                    row["employee"],
                    row["email"],
                    row["date"],
                    row["time"],
                    row["action"],
                    row["method"],
                    row["source"],
                    row["created_at"],
                ]
            )
        filename = f"attendance-{site.get('name') or 'site'}-{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        safe_filename = re.sub(r"[^0-9A-Za-z._-]+", "-", filename)
        response = app.response_class(buffer.getvalue(), mimetype="text/csv")
        response.headers["Content-Disposition"] = f'attachment; filename="{safe_filename}"'
        return response

    @app.route("/client/attendance/records", methods=["GET"])
    def client_attendance_records():
        user = _current_user()
        _require_client_user(user)
        client_id, site_id, site, _client = _client_site_context(user)
        start_raw = (request.args.get("from") or "").strip()
        end_raw = (request.args.get("to") or "").strip()
        if not start_raw or not end_raw:
            return jsonify(ok=False, message="Rentang tanggal wajib diisi."), 400
        date_from = _normalize_date_input(start_raw)
        date_to = _normalize_date_input(end_raw)
        if not date_from or not date_to:
            return jsonify(ok=False, message="Rentang tanggal tidak valid."), 400
        if date_from > date_to:
            date_from, date_to = date_to, date_from

        employees = _list_employees_by_site(site_id)
        allowed_emails = {
            (row.get("email") or "").strip().lower()
            for row in employees
            if (row.get("email") or "").strip()
        }

        rows = _attendance_rows_for_emails(
            allowed_emails,
            date_from=date_from,
            date_to=date_to,
        )
        aggregated_rows = _aggregate_attendance_records(rows)
        sanitized: list[dict] = []
        max_rows = 250
        for row in aggregated_rows[:max_rows]:
            sanitized.append(
                {
                    "employee": row["employee"] or "-",
                    "date": _format_display_date(row["date"]),
                    "check_in": row["check_in"] or "-",
                    "check_out": row["check_out"] or "-",
                    "method": row["method"] or "-",
                }
            )
        return jsonify(ok=True, data=sanitized, total=len(sanitized))

    @app.route("/client/policies/create", methods=["POST"])
    def client_policies_create():
        user = _current_user()
        _require_client_admin(user)
        _client_id, site_id, _site, _client = _client_site_context(user)
        effective_from_raw = (request.form.get("effective_from") or "").strip()
        effective_to_raw = (request.form.get("effective_to") or "").strip()
        work_duration_raw = (request.form.get("work_duration_minutes") or "").strip()
        grace_raw = (request.form.get("grace_minutes") or "").strip()
        late_raw = (request.form.get("late_threshold_minutes") or "").strip()
        allow_gps = 1 if request.form.get("allow_gps") == "1" else 0
        require_selfie = 1 if request.form.get("require_selfie") == "1" else 0
        allow_qr = 1 if request.form.get("allow_qr") == "1" else 0
        auto_checkout = 1 if request.form.get("auto_checkout") == "1" else 0
        cutoff_time = (request.form.get("cutoff_time") or "").strip()
        effective_from = _normalize_date_input(effective_from_raw)
        if not effective_from:
            flash("Tanggal mulai wajib format DD-MM-YYYY (contoh 01-02-2026) atau 1 Feb 2026.")
            return redirect(url_for("dashboard_client", _anchor="policies"))
        effective_to = _normalize_date_input(effective_to_raw) if effective_to_raw else None
        if effective_to_raw and not effective_to:
            flash("Tanggal selesai wajib format DD-MM-YYYY (contoh 01-02-2026) atau 1 Feb 2026.")
            return redirect(url_for("dashboard_client", _anchor="policies"))
        work_duration = int(work_duration_raw) if work_duration_raw.isdigit() else None
        grace_minutes = int(grace_raw) if grace_raw.isdigit() else None
        late_minutes = int(late_raw) if late_raw.isdigit() else None
        policy_id = _create_policy(
            scope_type="SITE",
            client_id=None,
            site_id=site_id,
            shift_id=None,
            effective_from=effective_from,
            effective_to=effective_to or None,
            work_duration_minutes=work_duration,
            grace_minutes=grace_minutes,
            late_threshold_minutes=late_minutes,
            allow_gps=allow_gps,
            require_selfie=require_selfie,
            allow_qr=allow_qr,
            auto_checkout=auto_checkout,
            cutoff_time=cutoff_time or None,
        )
        _log_audit_event(
            entity_type="policy",
            entity_id=policy_id,
            action="CREATE",
            actor=user,
            summary="Policy site dibuat dari dashboard client.",
            details={
                "site_id": site_id,
                "effective_from": effective_from,
                "effective_to": effective_to,
            },
        )
        flash("Policy berhasil ditambahkan.")
        return redirect(url_for("dashboard_client", _anchor="policies"))

    @app.route("/client/policies/<int:policy_id>/update", methods=["POST"])
    def client_policies_update(policy_id: int):
        user = _current_user()
        _require_client_admin(user)
        _client_id, site_id, _site, _client = _client_site_context(user)
        before = _get_policy_by_id(policy_id)
        if not before or int(before.get("site_id") or 0) != site_id:
            flash("Policy tidak ditemukan.")
            return redirect(url_for("dashboard_client", _anchor="policies"))
        effective_from_raw = (request.form.get("effective_from") or "").strip()
        effective_to_raw = (request.form.get("effective_to") or "").strip()
        work_duration_raw = (request.form.get("work_duration_minutes") or "").strip()
        grace_raw = (request.form.get("grace_minutes") or "").strip()
        late_raw = (request.form.get("late_threshold_minutes") or "").strip()
        allow_gps = 1 if request.form.get("allow_gps") == "1" else 0
        require_selfie = 1 if request.form.get("require_selfie") == "1" else 0
        allow_qr = 1 if request.form.get("allow_qr") == "1" else 0
        auto_checkout = 1 if request.form.get("auto_checkout") == "1" else 0
        cutoff_time = (request.form.get("cutoff_time") or "").strip()
        effective_from = _normalize_date_input(effective_from_raw)
        if not effective_from:
            flash("Tanggal mulai wajib format DD-MM-YYYY (contoh 01-02-2026) atau 1 Feb 2026.")
            return redirect(url_for("dashboard_client", _anchor="policies"))
        effective_to = _normalize_date_input(effective_to_raw) if effective_to_raw else None
        if effective_to_raw and not effective_to:
            flash("Tanggal selesai wajib format DD-MM-YYYY (contoh 01-02-2026) atau 1 Feb 2026.")
            return redirect(url_for("dashboard_client", _anchor="policies"))
        work_duration = int(work_duration_raw) if work_duration_raw.isdigit() else None
        grace_minutes = int(grace_raw) if grace_raw.isdigit() else None
        late_minutes = int(late_raw) if late_raw.isdigit() else None
        _update_policy(
            policy_id=policy_id,
            scope_type="SITE",
            client_id=None,
            site_id=site_id,
            shift_id=before.get("shift_id"),
            effective_from=effective_from,
            effective_to=effective_to or None,
            work_duration_minutes=work_duration,
            grace_minutes=grace_minutes,
            late_threshold_minutes=late_minutes,
            allow_gps=allow_gps,
            require_selfie=require_selfie,
            allow_qr=allow_qr,
            auto_checkout=auto_checkout,
            cutoff_time=cutoff_time or None,
        )
        _log_audit_event(
            entity_type="policy",
            entity_id=policy_id,
            action="UPDATE",
            actor=user,
            summary="Policy site diperbarui dari dashboard client.",
            details={"site_id": site_id},
        )
        flash("Policy berhasil diperbarui.")
        return redirect(url_for("dashboard_client", _anchor="policies"))

    @app.route("/client/policies/<int:policy_id>/end", methods=["POST"])
    def client_policies_end(policy_id: int):
        user = _current_user()
        _require_client_admin(user)
        _client_id, site_id, _site, _client = _client_site_context(user)
        before = _get_policy_by_id(policy_id)
        if not before or int(before.get("site_id") or 0) != site_id:
            flash("Policy tidak ditemukan.")
            return redirect(url_for("dashboard_client", _anchor="policies"))
        _end_policy(policy_id)
        _log_audit_event(
            entity_type="policy",
            entity_id=policy_id,
            action="END",
            actor=user,
            summary="Policy site ditutup dari dashboard client.",
            details={"site_id": site_id},
        )
        flash("Policy ditutup.")
        return redirect(url_for("dashboard_client", _anchor="policies"))

    @app.route("/client/users/create", methods=["POST"])
    def client_users_create():
        user = _current_user()
        _require_client_admin(user)
        client_id, site_id, _site, _client = _client_site_context(user)
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        role = (request.form.get("role") or "client_assistant").strip()
        password = (request.form.get("password") or "").strip()
        if not name:
            flash("Nama wajib diisi.")
            return redirect(url_for("dashboard_client", _anchor="settings"))
        if not _looks_like_email(email):
            flash("Email tidak valid.")
            return redirect(url_for("dashboard_client", _anchor="settings"))
        if role not in CLIENT_ROLE_OPTIONS:
            flash("Role tidak valid.")
            return redirect(url_for("dashboard_client", _anchor="settings"))
        if _get_user_by_email(email):
            flash("Email sudah terdaftar.")
            return redirect(url_for("dashboard_client", _anchor="settings"))
        if len(password) < 6:
            flash("Password awal minimal 6 karakter.")
            return redirect(url_for("dashboard_client", _anchor="settings"))
        if role == "client_admin":
            existing_admin = [
                u
                for u in _client_users_for_site(client_id, site_id)
                if u.get("role") == "client_admin"
            ]
            if existing_admin:
                flash("Client admin sudah ada untuk site ini.")
                return redirect(url_for("dashboard_client", _anchor="settings"))
        _create_user(
            name=name,
            email=email,
            role=role,
            password=password,
            client_id=client_id,
            site_id=site_id,
            must_change_password=1,
        )
        flash("User client berhasil ditambahkan.")
        return redirect(url_for("dashboard_client", _anchor="settings"))

    @app.route("/client/users/<int:user_id>/toggle", methods=["POST"])
    def client_users_toggle(user_id: int):
        user = _current_user()
        _require_client_admin(user)
        client_id, site_id, _site, _client = _client_site_context(user)
        target = _get_user_by_id(user_id)
        if not target:
            flash("User tidak ditemukan.")
            return redirect(url_for("dashboard_client", _anchor="settings"))
        if target["role"] not in CLIENT_ROLES:
            flash("User tidak valid.")
            return redirect(url_for("dashboard_client", _anchor="settings"))
        if int(_row_get(target, "client_id") or 0) != client_id or int(_row_get(target, "site_id") or 0) != site_id:
            flash("User tidak sesuai site.")
            return redirect(url_for("dashboard_client", _anchor="settings"))
        is_active = 0 if int(target["is_active"] or 0) == 1 else 1
        _update_user_basic(
            user_id=user_id,
            name=target["name"] or "",
            role=target["role"],
            is_active=is_active,
        )
        flash("Status user diperbarui.")
        return redirect(url_for("dashboard_client", _anchor="settings"))

    @app.route("/dashboard/manual_attendance", methods=["GET", "POST"])
    def manual_attendance():
        user = _current_user()
        if not user or not _can_submit_manual(user):
            return abort(403)
        employees = _employees()
        error = None
        success = None
        form_data = {}

        if request.method == "POST":
            form_data = request.form.to_dict()
            employee_id = (form_data.get("employee_id") or "").strip()
            date = (form_data.get("date") or "").strip()
            time = (form_data.get("time") or "").strip()
            action = (form_data.get("action") or "").strip().upper()
            reason = (form_data.get("reason") or "").strip()

            if not employee_id:
                error = "Pegawai wajib dipilih."
            elif not date or not time:
                error = "Tanggal dan waktu wajib diisi."
            elif action not in {"IN", "OUT"}:
                error = "Tipe presensi wajib dipilih."
            elif not reason:
                error = "Alasan wajib diisi."
            else:
                employee = _employee_by_id(employee_id)
                if not employee:
                    error = "Pegawai tidak ditemukan."
                elif not _approver_can_handle(user, employee.get("email") or ""):
                    error = "Anda tidak memiliki akses untuk pegawai ini."
                else:
                    _create_manual_request(
                        employee=employee,
                        date=date,
                        time=time,
                        action=action,
                        reason=reason,
                        created_by=user,
                    )
                    success = "Manual attendance terkirim (pending)."
                    form_data = {}

        return render_template(
            "dashboard/manual_attendance.html",
            user=user,
            employees=employees,
            error=error,
            success=success,
            form=form_data,
        )

    @app.route("/logout", methods=["POST"])
    def logout():
        session.clear()
        return redirect("/")

    @app.route("/api/attendance/checkin", methods=["POST"])
    def attendance_checkin():
        """
        FLOW LOGIC KONSISTENSI (4 LAYER):
        
        Layer 1 (Policies): Resolved dari site/client/shift -> define allow_gps, allow_qr, require_selfie
        Layer 2 (Assignment): User harus punya active assignment (site + shift)
        Layer 3 (Dashboard Method Selection): User pilih method: gps, gps_selfie, atau qr
        Layer 4 (Validation Rules):
          - GPS mode: require location (lat, lng), selfie TIDAK required
          - GPS+Selfie mode: require location + selfie
          - QR mode: require QR code, location TIDAK required
          - Policy require_selfie: HANYA apply untuk gps_selfie method
        
        Konsistensi Logic:
        ✓ Frontend updatePresenceReadiness() harus match backend validation
        ✓ Policy allow_gps/allow_qr harus restrict method selection
        ✓ Method-specific requirements harus consistent
        ✓ Selfie requirement ONLY untuk gps_selfie, bukan untuk GPS mode
        """
        try:
            user = _current_user()
        except Exception as e:
            return jsonify(ok=False, message="Error mendapatkan user."), 400
            
        forbidden = _require_api_role(user, EMPLOYEE_ROLES)
        if forbidden:
            return forbidden
            
        try:
            employee = _employee_by_email(user.email, only_active=False)
        except Exception as e:
            return jsonify(ok=False, message=f"Error cari employee: {str(e)}"), 400
            
        if not employee:
            return jsonify(ok=False, message="Lengkapi data master pegawai terlebih dahulu."), 400
            
        try:
            assignment = _get_active_assignment(user.id)
        except Exception as e:
            return jsonify(ok=False, message=f"Error cari assignment: {str(e)}"), 400
            
        if not assignment:
            return jsonify(ok=False, message="Belum ada penempatan aktif. Hubungi admin."), 400
        
        site = _get_site_by_id(assignment.get("site_id"))
        
        if not site:
            return jsonify(ok=False, message="Site penempatan tidak ditemukan. Hubungi admin."), 400
        
        # Convert sqlite3.Row to dict for easier access
        site = dict(site) if hasattr(site, 'keys') else site
        
        if int(site.get("is_active") or 0) != 1:
            return jsonify(ok=False, message="Site penempatan sedang nonaktif."), 400
        
        policy = _resolve_attendance_policy(
            site.get("id"),
            site.get("client_id"),
            assignment.get("shift_id") if assignment else None,
        )
        
        today = _today_key()
        
        try:
            checkin_exists = _attendance_action_exists(user.email, today, "checkin")
            if checkin_exists:
                return jsonify(ok=False, message="Sudah check-in hari ini."), 400
        except Exception as e:
            return jsonify(ok=False, message=f"Error cek absen: {str(e)}"), 400
        
        try:
            checkout_exists = _attendance_action_exists(user.email, today, "checkout")
            if checkout_exists:
                return jsonify(ok=False, message="Check-out sudah tercatat hari ini."), 400
        except Exception as e:
            return jsonify(ok=False, message=f"Error cek checkout: {str(e)}"), 400
        
        data = request.form or {}
        method = (data.get("method") or "gps_selfie").strip()
        lat = (data.get("lat") or "").strip()
        lng = (data.get("lng") or data.get("lon") or "").strip()
        accuracy = (data.get("accuracy") or "").strip()
        device_time = (data.get("device_time") or "").strip()
        qr_data = (data.get("qr_data") or "").strip()
        
        selfie_file = request.files.get("selfie")

        if method not in {"gps_selfie", "gps", "qr"}:
            return jsonify(ok=False, message="Metode presensi tidak dikenal."), 400
        if not policy.get("allow_gps", 1) and method in {"gps", "gps_selfie"}:
            return jsonify(ok=False, message="Metode GPS tidak diizinkan."), 400
        if not policy.get("allow_qr", 1) and method == "qr":
            return jsonify(ok=False, message="Metode QR tidak diizinkan."), 400
        
        # Validate location for GPS-based methods only
        if method in {"gps", "gps_selfie"}:
            if not lat or not lng:
                return jsonify(ok=False, message="Lokasi GPS wajib diisi."), 400
            try:
                lat_f = float(lat)
                lng_f = float(lng)
            except ValueError:
                return jsonify(ok=False, message="Lokasi GPS tidak valid."), 400
            if not _within_site_radius(lat_f, lng_f, site):
                return jsonify(ok=False, message="Lokasi di luar radius site."), 400
        
        # Validate selfie for GPS+Selfie method (policy-based)
        if method == "gps_selfie" and int(policy.get("require_selfie", 1) or 0) == 1:
            if not selfie_file or not selfie_file.filename:
                print(f"[CHECKIN] Missing selfie for gps_selfie")
                return jsonify(ok=False, message="Selfie wajib untuk presensi."), 400
            print(f"[CHECKIN] Selfie validation passed")
        
        # Validate QR data for QR method only
        if method == "qr":
            if not qr_data:
                print(f"[CHECKIN] Missing QR data")
                return jsonify(ok=False, message="QR code wajib di-scan."), 400
            ok, msg = _validate_qr_data(qr_data, site["client_id"], "IN")
            if not ok:
                print(f"[CHECKIN] Invalid QR: {msg}")
                return jsonify(ok=False, message=msg), 400
            print(f"[CHECKIN] QR validation passed")


        
        # Validate QR data for QR method only
        if method == "qr":
            if not qr_data:
                return jsonify(ok=False, message="QR code wajib di-scan."), 400
            ok, msg = _validate_qr_data(qr_data, site["client_id"], "IN")
            if not ok:
                return jsonify(ok=False, message=msg), 400
        selfie_path = None
        if selfie_file and selfie_file.filename:
            try:
                selfie_path = _save_upload(selfie_file, "uploads/attendance", 10 * 1024 * 1024)
            except ValueError as err:
                return jsonify(ok=False, message=str(err)), 400

        try:
            record = _create_attendance_record(
                employee=employee,
                employee_email=user.email,
                action="checkin",
                method="gps+selfie" if method == "gps_selfie" else method,
                device_time=device_time,
                source="app",
                selfie_path=selfie_path,
            )
        except sqlite3.IntegrityError as e:
            # Handle UNIQUE constraint violation (sudah checkin hari ini)
            if "UNIQUE constraint failed" in str(e):
                return jsonify(ok=False, message="Sudah check-in hari ini."), 400
            return jsonify(ok=False, message=f"Error mencatat presensi: {str(e)}"), 400
        except Exception as e:
            return jsonify(ok=False, message=f"Error mencatat presensi: {str(e)}"), 500
        
        _log_audit_event(
            entity_type="attendance",
            entity_id=record.get("id"),
            action="CHECKIN",
            actor=user,
            summary="Check-in tercatat.",
            details={"method": record.get("method"), "date": record.get("date"), "time": record.get("time")},
        )
        return jsonify(ok=True, message="Presensi tercatat.", data=record), 200

    @app.route("/api/attendance/checkout", methods=["POST"])
    def attendance_checkout():
        user = _current_user()
        forbidden = _require_api_role(user, EMPLOYEE_ROLES)
        if forbidden:
            return forbidden
        employee = _employee_by_email(user.email, only_active=False)
        if not employee:
            return jsonify(ok=False, message="Lengkapi data master pegawai terlebih dahulu."), 400
        assignment = _get_active_assignment(user.id)
        if not assignment:
            return jsonify(ok=False, message="Belum ada penempatan aktif. Hubungi admin."), 400
        site = _get_site_by_id(assignment.get("site_id"))
        if not site:
            return jsonify(ok=False, message="Site penempatan tidak ditemukan. Hubungi admin."), 400
        if int(site["is_active"] or 0) != 1:
            return jsonify(ok=False, message="Site penempatan sedang nonaktif."), 400
        policy = _resolve_attendance_policy(
            site["id"] if site else None,
            site["client_id"] if site else None,
            assignment.get("shift_id") if assignment else None,
        )
        today = _today_key()
        if not _attendance_action_exists(user.email, today, "checkin"):
            return jsonify(ok=False, message="Belum ada check-in hari ini."), 400
        if _attendance_action_exists(user.email, today, "checkout"):
            return jsonify(ok=False, message="Check-out sudah tercatat hari ini."), 400
        data = request.form or {}
        method = (data.get("method") or "gps_selfie").strip()
        lat = (data.get("lat") or "").strip()
        lng = (data.get("lng") or data.get("lon") or "").strip()
        accuracy = (data.get("accuracy") or "").strip()
        device_time = (data.get("device_time") or "").strip()
        qr_data = (data.get("qr_data") or "").strip()
        selfie_file = request.files.get("selfie")

        if method not in {"gps_selfie", "gps", "qr"}:
            return jsonify(ok=False, message="Metode presensi tidak dikenal."), 400
        if not policy.get("allow_gps", 1) and method in {"gps", "gps_selfie"}:
            return jsonify(ok=False, message="Metode GPS tidak diizinkan."), 400
        if not policy.get("allow_qr", 1) and method == "qr":
            return jsonify(ok=False, message="Metode QR tidak diizinkan."), 400
        
        # Validate location for GPS-based methods only
        if method in {"gps", "gps_selfie"}:
            if not lat or not lng:
                return jsonify(ok=False, message="Lokasi GPS wajib diisi."), 400
            try:
                lat_f = float(lat)
                lng_f = float(lng)
            except ValueError:
                return jsonify(ok=False, message="Lokasi GPS tidak valid."), 400
            if not _within_site_radius(lat_f, lng_f, site):
                return jsonify(ok=False, message="Lokasi di luar radius site."), 400
        
        # Validate selfie for GPS+Selfie method (policy-based)
        if method == "gps_selfie" and int(policy.get("require_selfie", 1) or 0) == 1:
            if not selfie_file or not selfie_file.filename:
                return jsonify(ok=False, message="Selfie wajib untuk presensi."), 400
        
        # Validate QR data for QR method only
        if method == "qr":
            if not qr_data:
                return jsonify(ok=False, message="QR code wajib di-scan."), 400
            ok, msg = _validate_qr_data(qr_data, site["client_id"], "OUT")
            if not ok:
                return jsonify(ok=False, message=msg), 400
        selfie_path = None
        if selfie_file and selfie_file.filename:
            try:
                selfie_path = _save_upload(selfie_file, "uploads/attendance", 10 * 1024 * 1024)
            except ValueError as err:
                return jsonify(ok=False, message=str(err)), 400

        record = _create_attendance_record(
            employee=employee,
            employee_email=user.email,
            action="checkout",
            method="gps+selfie" if method == "gps_selfie" else method,
            device_time=device_time,
            source="app",
            selfie_path=selfie_path,
        )
        _log_audit_event(
            entity_type="attendance",
            entity_id=record.get("id"),
            action="CHECKOUT",
            actor=user,
            summary="Check-out tercatat.",
            details={"method": record.get("method"), "date": record.get("date"), "time": record.get("time")},
        )
        return jsonify(ok=True, message="Check-out tercatat.", data=record), 200

    @app.route("/api/attendance/today", methods=["GET"])
    def attendance_today():
        user = _current_user()
        print("[API] /api/attendance/today user:", user.email if user else None)
        forbidden = _require_api_role(user, EMPLOYEE_ROLES)
        if forbidden:
            print("[API] Forbidden for user", user.email if user else None)
            return forbidden
        today = _today_key()
        print("[API] Today key:", today)
        records = _list_attendance_today(user.email, today, limit=10)
        print(f"[API] Attendance records for {user.email} on {today}: {records}")
        return jsonify(ok=True, data=records), 200

    @app.route("/api/attendance/summary", methods=["GET"])
    def attendance_summary():
        user = _current_user()
        if not user:
            return _json_forbidden()
        month_param = (request.args.get("month") or "").strip()
        month_value = month_param if month_param else None
        data = _attendance_month_summary_for_user(user, month_value)
        return jsonify(ok=True, data=data), 200

    @app.route("/api/attendance/manual", methods=["POST"])
    def attendance_manual():
        user = _current_user()
        forbidden = _require_api_role(user, ADMIN_ROLES)
        if forbidden:
            return forbidden
        if not _can_submit_manual(user):
            return _json_forbidden()
        data = _get_json()
        employee_email = (data.get("employee_email") or "").strip()
        action = (data.get("action") or "IN").strip().upper()
        reason = (data.get("reason") or "").strip()
        date_value = (data.get("date") or "").strip()
        time_value = (data.get("time") or "").strip()

        if not _looks_like_email(employee_email):
            return jsonify(ok=False, message="Email pegawai wajib diisi."), 400
        if action not in {"IN", "OUT"}:
            return jsonify(ok=False, message="Tipe presensi wajib dipilih."), 400
        if not reason:
            return jsonify(ok=False, message="Alasan wajib diisi."), 400
        employee = _employee_by_email(employee_email, only_active=False)
        if not employee:
            return jsonify(ok=False, message="Data pegawai tidak ditemukan."), 404
        if not _approver_can_handle(user, employee.get("email") or ""):
            return _json_forbidden()
        if not date_value:
            date_value = _today_key()
        if not time_value:
            time_value = datetime.now().strftime("%H:%M")
        _create_manual_request(
            employee=employee,
            date=date_value,
            time=time_value,
            action=action,
            reason=reason,
            created_by=user,
        )
        return jsonify(ok=True, message="Pengajuan manual attendance terkirim."), 200

    @app.route("/api/attendance/pending", methods=["GET"])
    def attendance_pending():
        user = _current_user()
        forbidden = _require_api_role(user, ADMIN_ROLES)
        if forbidden:
            return forbidden
        items = _fetch_manual_requests("pending", user)
        return jsonify(ok=True, data=items), 200

    @app.route("/api/attendance/approve", methods=["POST"])
    def attendance_approve():
        user = _current_user()
        forbidden = _require_api_role(user, ADMIN_ROLES)
        if forbidden:
            return forbidden
        data = _get_json()
        rid = data.get("id")
        note = (data.get("note") or "").strip()
        try:
            request_id = int(rid)
        except (TypeError, ValueError):
            return jsonify(ok=False, message="ID tidak valid."), 400
        request_row = _manual_request_by_id(request_id)
        if not request_row:
            return jsonify(ok=False, message="Data attendance tidak ditemukan."), 404
        if _row_get(request_row, "status") != "PENDING":
            return jsonify(ok=False, message="Attendance sudah diproses."), 400
        if not _approver_can_handle(user, _row_get(request_row, "employee_email") or ""):
            return _json_forbidden()
        ok, message = _approve_manual_request_atomic(request_id, user, note or None)
        if not ok:
            return jsonify(ok=False, message=message), 400
        return jsonify(ok=True, message="Manual attendance disetujui."), 200

    @app.route("/api/leave/request", methods=["POST"])
    def leave_request():
        user = _current_user()
        forbidden = _require_api_role(user, EMPLOYEE_ROLES)
        if forbidden:
            return forbidden
        if request.is_json:
            data = _get_json()
        else:
            data = request.form or {}
        leave_type = (data.get("type") or "").strip()
        date_from = (data.get("date_from") or "").strip()
        date_to = (data.get("date_to") or "").strip()
        reason = (data.get("reason") or "").strip()
        attachment = (data.get("attachment") or "").strip()
        attachment_base64 = data.get("attachment_base64")
        attachment_file = request.files.get("attachment")

        if leave_type not in {"izin", "sakit"}:
            return jsonify(ok=False, message="Tipe izin tidak valid."), 400
        if not date_from or not date_to:
            return jsonify(ok=False, message="Tanggal izin wajib diisi."), 400
        if not reason:
            return jsonify(ok=False, message="Alasan wajib diisi."), 400

        attachment_path = None
        if attachment_file and attachment_file.filename:
            try:
                attachment_path = _save_leave_attachment(
                    attachment_file,
                    "uploads/leave",
                    2 * 1024 * 1024,
                )
            except ValueError as err:
                return jsonify(ok=False, message=str(err)), 400
            attachment = attachment_file.filename
        elif attachment_base64:
            try:
                attachment_path = _save_base64_attachment(
                    attachment_base64,
                    "uploads/leave",
                    2 * 1024 * 1024,
                )
            except ValueError as err:
                return jsonify(ok=False, message=str(err)), 400

        request_id = _create_leave_request(
            employee_email=user.email,
            leave_type=leave_type,
            date_from=date_from,
            date_to=date_to,
            reason=reason,
            attachment=attachment,
            attachment_path=attachment_path,
        )
        record = _get_leave_request_by_id(request_id) or {}
        return jsonify(ok=True, message="Pengajuan izin dikirim.", data=record), 200

    @app.route("/api/leave/my", methods=["GET"])
    def leave_my():
        user = _current_user()
        forbidden = _require_api_role(user, EMPLOYEE_ROLES)
        if forbidden:
            return forbidden
        mine = _list_leave_requests_by_email(user.email)
        return jsonify(ok=True, data=mine), 200

    @app.route("/api/leave/pending", methods=["GET"])
    def leave_pending():
        user = _current_user()
        if not user or not _can_approve_leave(user):
            return _json_forbidden()
        limit = request.args.get("limit")
        try:
            limit_value = int(limit) if limit is not None else None
        except ValueError:
            limit_value = None
        pending = _list_leave_pending(user, limit=limit_value)
        return jsonify(ok=True, data=pending), 200

    @app.route("/api/leave/approve", methods=["POST"])
    def leave_approve():
        user = _current_user()
        if not user or not _can_approve_leave(user):
            return _json_forbidden()
        data = _get_json()
        rid = data.get("id")
        action = (data.get("action") or "approve").strip().lower()
        note = (data.get("note") or "").strip()
        if action not in {"approve", "reject"}:
            return jsonify(ok=False, message="Aksi tidak valid."), 400
        try:
            request_id = int(rid)
        except (TypeError, ValueError):
            return jsonify(ok=False, message="ID tidak valid."), 400
        record = _get_leave_request_by_id(request_id)
        if not record:
            return jsonify(ok=False, message="Pengajuan tidak ditemukan."), 404
        if (record.get("status") or "").lower() != "pending":
            return jsonify(ok=False, message="Pengajuan sudah diproses."), 400
        if not _approver_can_handle(user, record.get("employee_email") or ""):
            return _json_forbidden()
        if action == "reject" and not note:
            return jsonify(ok=False, message="Alasan penolakan wajib diisi."), 400

        status = "rejected" if action == "reject" else "approved"
        _update_leave_request_status(
            request_id=request_id,
            status=status,
            approver_email=user.email,
            note=note or None,
        )
        _log_audit_event(
            entity_type="leave_request",
            entity_id=request_id,
            action="APPROVE" if status == "approved" else "REJECT",
            actor=user,
            summary="Pengajuan izin diproses.",
            details={"status": status, "note": note or None},
        )
        message = "Pengajuan ditolak." if action == "reject" else "Pengajuan disetujui."
        return jsonify(ok=True, message=message), 200

    return app


def _looks_like_email(value: str) -> bool:
    if not value:
        return False
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value))


def _normalize_phone(value: str) -> str:
    if not value:
        return ""
    return re.sub(r"\D", "", value)


def _validate_login(data: Dict[str, str]) -> AuthResult:
    login_type = (data.get("login_type") or "email").strip().lower()
    identifier = (data.get("identifier") or data.get("email") or data.get("phone") or "").strip()
    password = data.get("password", "")
    theme = data.get("theme", "dark")

    if login_type == "phone":
        phone = _normalize_phone(identifier)
        if not phone:
            return AuthResult(False, "Isi nomor telp dulu.")
        employee = _employee_by_phone(phone, only_active=False)
        if not employee:
            return AuthResult(False, "No telp tidak ditemukan.")
        email = (employee.get("email") or "").strip()
        if not email:
            return AuthResult(False, "Email akun tidak ditemukan.")
    else:
        email = identifier
        if not _looks_like_email(email):
            return AuthResult(False, "Isi email dengan benar.")
    if not password:
        return AuthResult(False, "Isi password dulu.")

    row = _get_user_by_email(email)
    if not row:
        return AuthResult(False, "Akun tidak ditemukan.")
    if int(row["is_active"] or 0) != 1:
        return AuthResult(False, "Akun tidak aktif.")
    if not check_password_hash(row["password_hash"], password):
        return AuthResult(False, "Password salah.")
    if row["role"] == "employee":
        employee = _employee_by_email(email, only_active=False)
        if employee and int(employee.get("is_active") or 0) != 1:
            return AuthResult(False, "Akun pegawai belum aktif.")
    user = _user_row_to_user(row, theme)
    _persist_user(user)

    if user.role in CLIENT_ROLES:
        target = "/dashboard/client"
    elif user.role in ADMIN_ROLES:
        target = "/dashboard/admin"
    else:
        target = "/dashboard/pegawai"
    return AuthResult(True, f"Login (demo). Tema {theme}.", target)


def _get_json() -> Dict[str, str]:
    if request.is_json:
        return request.get_json(force=True) or {}
    return request.form.to_dict() if request.form else {}


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("PRESENSI_DB_PATH") or os.path.join(BASE_DIR, "presensi.db")
_seed_flag = os.environ.get("ENABLE_SEED_DATA")
if _seed_flag is None:
    ENABLE_SEED_DATA = True
else:
    ENABLE_SEED_DATA = _seed_flag.lower() in {"1", "true", "yes"}


# =========================
# Demo data & helpers
# =========================
ADMIN_ROLES = {"hr_superadmin", "manager_operational", "supervisor", "admin_asistent"}
CLIENT_ROLES = {"client_admin", "client_assistant", "client_supervisor", "client_operational"}
EMPLOYEE_ROLES = {"employee"}
APPROVER_ROLES = {"hr_superadmin", "manager_operational", "supervisor"}
SEED_USERS: list[dict] = []
SEED_USERS_JSON = (os.environ.get("SEED_USERS_JSON") or "").strip()
if not SEED_USERS_JSON:
    SEED_USERS = [
        {
            "email": "hrd@gmi.com",
            "name": "HR Superadmin",
            "role": "hr_superadmin",
            "password": "hrd123",
        }
    ]
else:
    try:
        SEED_USERS = json.loads(SEED_USERS_JSON)
    except json.JSONDecodeError as exc:
        raise RuntimeError("SEED_USERS_JSON tidak valid.") from exc
SEED_EMPLOYEES = [
]
ADMIN_ROLE_OPTIONS = ["hr_superadmin", "manager_operational", "supervisor", "admin_asistent"]
CLIENT_ROLE_OPTIONS = ["client_admin", "client_assistant", "client_supervisor", "client_operational"]
ROLE_OPTIONS = ADMIN_ROLE_OPTIONS + CLIENT_ROLE_OPTIONS + ["employee"]
ROLE_PERMISSION_KEYS = [
    "view_overview",
    "manage_clients_view",
    "manage_clients_add",
    "manage_clients_actions",
    "manage_sites",
    "manage_shifts",
    "manage_employees_view",
    "manage_employees_add",
    "manage_employees_actions",
    "manage_assignments",
    "manage_policies",
    "view_attendance",
    "approve_requests",
    "manage_settings_codes",
    "manage_settings_password",
]
ROLE_PERMISSION_LABELS = {
    "view_overview": "Overview",
    "manage_clients_view": "Clients: Lihat",
    "manage_clients_add": "Clients: Tambah",
    "manage_clients_actions": "Clients: Aksi (Edit/Hapus)",
    "manage_sites": "Sites",
    "manage_shifts": "Shifts",
    "manage_employees_view": "Employees: Lihat",
    "manage_employees_add": "Employees: Tambah",
    "manage_employees_actions": "Employees: Aksi (Edit/Hapus)",
    "manage_assignments": "Assignments",
    "manage_policies": "Policies",
    "view_attendance": "Attendance",
    "approve_requests": "Approvals",
    "manage_settings_codes": "Setting: Kode Reg",
    "manage_settings_password": "Setting: Password",
}
DEMO_GPS_CENTER = (-6.5706, 107.7603)
DEMO_GPS_RADIUS_METERS = 100
DEMO_QR_PREFIX = "GMI"
QR_WINDOW_SECONDS = 12 * 60 * 60
DEFAULT_CLIENT_PASSWORD = "client@123"
DEFAULT_ATTENDANCE_POLICY = {
    "work_duration_minutes": None,
    "grace_minutes": None,
    "late_threshold_minutes": None,
    "allow_gps": 1,
    "require_selfie": 0,
    "allow_qr": 1,
    "auto_checkout": 0,
    "cutoff_time": None,
}


@dataclass
class User:
    id: int
    email: str
    role: str
    name: str = ""
    theme: str = "dark"
    selfie_path: str | None = None
    must_change_password: int = 0
    client_id: int | None = None
    site_id: int | None = None


def _persist_user(user: User) -> None:
    session["user"] = {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "name": user.name,
        "theme": user.theme,
        "selfie_path": user.selfie_path,
        "must_change_password": user.must_change_password,
        "client_id": user.client_id,
        "site_id": user.site_id,
    }


def _current_user() -> User | None:
    data = session.get("user") or {}
    if not data:
        return None
    user_id = int(data.get("id") or 0)
    if user_id:
        row = _get_user_by_id(user_id)
        if not row or int(row["is_active"] or 0) != 1:
            session.pop("user", None)
            return None
        role = row["role"] if "role" in row.keys() else data.get("role", "employee")
        email = row["email"] if "email" in row.keys() else data.get("email", "")
        name = row["name"] if "name" in row.keys() else data.get("name", "")
        client_id = row["client_id"] if "client_id" in row.keys() else data.get("client_id")
        site_id = row["site_id"] if "site_id" in row.keys() else data.get("site_id")
    else:
        role = data.get("role", "employee")
        email = data.get("email", "")
        name = data.get("name", "")
        client_id = data.get("client_id")
        site_id = data.get("site_id")
    return User(
        id=int(data.get("id") or 0),
        email=email,
        role=role,
        name=name,
        theme=data.get("theme", "dark"),
        selfie_path=data.get("selfie_path"),
        must_change_password=int(data.get("must_change_password") or 0),
        client_id=int(client_id) if str(client_id).isdigit() and int(client_id) > 0 else None,
        site_id=int(site_id) if str(site_id).isdigit() and int(site_id) > 0 else None,
    )


def _require_role(user: User | None, allowed_roles: set[str]) -> None:
    if not user or user.role not in allowed_roles:
        abort(403)


def _require_api_role(user: User | None, allowed_roles: set[str]):
    if not user or user.role not in allowed_roles:
        return _json_forbidden()
    return None


def _require_admin(user: User | None) -> None:
    _require_role(user, ADMIN_ROLES)


def _client_admin_client_id(user: User | None) -> int | None:
    if not user or user.role != "client_admin":
        return None
    if isinstance(user.client_id, int) and user.client_id > 0:
        return int(user.client_id)
    return None


def _approver_client_scope_id(user: User | None) -> int | None:
    if not user:
        return None
    if user.role == "client_admin":
        return _client_admin_client_id(user)
    if user.role == "manager_operational":
        if isinstance(user.client_id, int) and user.client_id > 0:
            return int(user.client_id)
    return None


def _client_user_client_id(user: User | None) -> int | None:
    if not user or user.role not in CLIENT_ROLES:
        return None
    if isinstance(user.client_id, int) and user.client_id > 0:
        return int(user.client_id)
    return None


def _client_user_site_id(user: User | None) -> int | None:
    if not user or user.role not in CLIENT_ROLES:
        return None
    if isinstance(user.site_id, int) and user.site_id > 0:
        return int(user.site_id)
    return None


def _require_client_user(user: User | None) -> None:
    if not user or user.role not in CLIENT_ROLES:
        abort(403)


def _require_client_admin(user: User | None) -> None:
    if not user or user.role != "client_admin":
        abort(403)


def _require_client_admin_client(user: User | None, client_id: int | None) -> None:
    if not user or user.role != "client_admin":
        return
    scope_id = _client_admin_client_id(user)
    if not scope_id or not client_id or int(client_id) != scope_id:
        abort(403)


def _require_client_admin_site(user: User | None, site_id: int | None) -> None:
    if not user or user.role != "client_admin":
        return
    site = _get_site_by_id(site_id) if site_id else None
    client_id = int(site["client_id"]) if site and site["client_id"] is not None else None
    _require_client_admin_client(user, client_id)


def _client_site_context(user: User | None) -> tuple[int, int, dict, dict]:
    _require_client_user(user)
    client_id = _client_user_client_id(user)
    site_id = _client_user_site_id(user)
    if not client_id or not site_id:
        abort(403)
    site_row = _get_site_by_id(site_id)
    if not site_row:
        abort(404)
    if int(_row_get(site_row, "client_id") or 0) != client_id:
        abort(403)
    client_row = _get_client_by_id(client_id)
    client = dict(client_row) if client_row else {"id": client_id, "name": "Client"}
    return client_id, site_id, dict(site_row), client


def _require_hr_or_client_admin(user: User | None) -> None:
    if not user or user.role not in ADMIN_ROLES:
        abort(403)


def _require_manual_approver(user: User | None) -> None:
    if not user or not _can_approve_manual(user):
        abort(403)


def _require_hr_superadmin(user: User | None) -> None:
    _require_role(user, {"hr_superadmin"})


def _json_forbidden():
    return jsonify(ok=False, message="Unauthorized."), 403


def _default_role_permissions(role: str) -> dict[str, bool]:
    defaults = {key: True for key in ROLE_PERMISSION_KEYS}
    if role == "hr_superadmin":
        return defaults
    if role in CLIENT_ROLES:
        for key in ROLE_PERMISSION_KEYS:
            defaults[key] = False
    defaults["manage_settings_codes"] = False
    defaults["manage_settings_password"] = False
    return defaults


def _get_role_permissions(role: str) -> dict[str, bool]:
    conn = _db_connect()
    try:
        if not _table_exists(conn, "role_permissions"):
            return _default_role_permissions(role)
        row = conn.execute(
            "SELECT permissions_json FROM role_permissions WHERE role = ?",
            (role,),
        ).fetchone()
        if not row:
            return _default_role_permissions(role)
        try:
            payload = json.loads(row["permissions_json"] or "{}")
        except json.JSONDecodeError:
            return _default_role_permissions(role)
        merged = _default_role_permissions(role)
        for key in ROLE_PERMISSION_KEYS:
            if key in payload:
                merged[key] = bool(payload[key])
        return merged
    finally:
        conn.close()


def _set_role_permissions(role: str, permissions: dict[str, bool]) -> None:
    if role == "hr_superadmin":
        permissions = {key: True for key in ROLE_PERMISSION_KEYS}
    payload = {key: bool(permissions.get(key)) for key in ROLE_PERMISSION_KEYS}
    conn = _db_connect()
    try:
        conn.execute(
            """
            INSERT INTO role_permissions (role, permissions_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(role) DO UPDATE SET
                permissions_json = excluded.permissions_json,
                updated_at = excluded.updated_at
            """,
            (role, json.dumps(payload, ensure_ascii=True), _now_ts()),
        )
    finally:
        conn.commit()
        conn.close()


def _has_role_permission(role: str, permission: str) -> bool:
    if role == "hr_superadmin":
        return True
    perms = _get_role_permissions(role)
    return bool(perms.get(permission))


def _permission_for_admin_endpoint(endpoint: str | None) -> str | None:
    if not endpoint:
        return None
    mapping = {
        "admin.overview": "view_overview",
        "admin.clients": "manage_clients_view",
        "admin.client_profile": "manage_clients_view",
        "admin.clients_create": "manage_clients_add",
        "admin.clients_update": "manage_clients_actions",
        "admin.clients_delete": "manage_clients_actions",
        "admin.client_contacts_create": "manage_clients_actions",
        "admin.client_contacts_update": "manage_clients_actions",
        "admin.client_contacts_primary": "manage_clients_actions",
        "admin.client_contacts_delete": "manage_clients_actions",
        "admin.sites": "manage_sites",
        "admin.settings_sites_create": "manage_sites",
        "admin.settings_sites_update": "manage_sites",
        "admin.settings_sites_toggle": "manage_sites",
        "admin.shifts": "manage_shifts",
        "admin.settings_shifts_create": "manage_shifts",
        "admin.settings_shifts_update": "manage_shifts",
        "admin.settings_shifts_toggle": "manage_shifts",
        "admin.employees": "manage_employees_view",
        "admin.employees_create": "manage_employees_add",
        "admin.employees_update": "manage_employees_actions",
        "admin.employees_delete": "manage_employees_actions",
        "admin.assignments": "manage_assignments",
        "admin.assignments_create": "manage_assignments",
        "admin.assignments_update": "manage_assignments",
        "admin.assignments_end": "manage_assignments",
        "admin.policies": "manage_policies",
        "admin.policies_create": "manage_policies",
        "admin.policies_update": "manage_policies",
        "admin.policies_end": "manage_policies",
        "admin.attendance": "view_attendance",
        "admin.approvals": "approve_requests",
        "admin.settings_registration_codes_create": "manage_settings_codes",
    }
    return mapping.get(endpoint)


def _now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _today_key() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _normalize_date_input(value: str | None) -> str | None:
    if not value:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    if "/" in raw:
        parts = raw.split("/")
        if len(parts) == 3 and all(part.isdigit() for part in parts):
            day, month, year = parts
            if len(year) == 4:
                try:
                    dt = datetime(int(year), int(month), int(day))
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    return None
        return None
    if "-" in raw:
        try:
            dt = datetime.strptime(raw, "%d-%m-%Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    try:
        dt = datetime.fromisoformat(raw)
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass
    for fmt in ("%d %b %Y", "%d %B %Y"):
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _date_from_input(value: str | None) -> datetime.date | None:
    normalized = _normalize_date_input(value)
    if not normalized:
        return None
    return datetime.fromisoformat(normalized).date()


def _device_time_parts(device_time: str | None) -> tuple[str, str]:
    if device_time:
        value = device_time.strip()
    else:
        value = ""
    if value:
        try:
            normalized = value.replace("Z", "+00:00")
            dt = datetime.fromisoformat(normalized)
            return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M")
        except ValueError:
            if " " in value:
                date_part, time_part = value.split(" ", 1)
                return date_part, time_part[:5]
    return _today_key(), datetime.now().strftime("%H:%M")


def _parse_hhmm(value: str | None) -> int | None:
    if not value:
        return None
    match = re.match(r"^\s*(\d{1,2}):(\d{2})\s*$", value)
    if not match:
        return None
    hour = int(match.group(1))
    minute = int(match.group(2))
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return None
    return hour * 60 + minute


def _extract_minutes(time_value: str | None, created_at: str | None) -> int | None:
    minutes = _parse_hhmm(time_value)
    if minutes is not None:
        return minutes
    if created_at and " " in created_at:
        return _parse_hhmm(created_at.split(" ")[1][:5])
    return None


def _date_in_range(target: str, start: str | None, end: str | None) -> bool:
    if not start or not end:
        return False
    return start <= target <= end


def _month_bounds(month_str: str | None = None) -> tuple[date, date]:
    if month_str:
        parts = month_str.split("-")
        if len(parts) == 2:
            try:
                year = int(parts[0])
                month = int(parts[1])
            except ValueError:
                year = None
                month = None
        else:
            year = None
            month = None
    else:
        year = None
        month = None
    now = datetime.now()
    if year is None or month is None or not (1 <= month <= 12):
        year, month = now.year, now.month
    _, last_day = calendar.monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)
    return start_date, end_date


def _count_overlap_days(
    start: date | None,
    end: date | None,
    window_start: date,
    window_end: date,
) -> int:
    if not start or not end:
        return 0
    lower = max(start, window_start)
    upper = min(end, window_end)
    if lower > upper:
        return 0
    return (upper - lower).days + 1


def _policy_active_for_date(policy: dict, today: str) -> bool:
    effective_from = (policy.get("effective_from") or "").strip()
    effective_to = (policy.get("effective_to") or "").strip()
    if effective_from and effective_from > today:
        return False
    if effective_to and effective_to < today:
        return False
    return True


def _list_active_assignments(today: str) -> list[dict]:
    conn = _db_connect()
    try:
        if not _table_exists(conn, "assignments"):
            return []
        cur = conn.execute(
            """
            SELECT
                a.employee_user_id,
                u.email AS employee_email,
                a.site_id,
                s.client_id,
                COALESCE(c.name, s.client_name) AS client_name
            FROM assignments a
            JOIN users u ON u.id = a.employee_user_id
            JOIN sites s ON s.id = a.site_id
            LEFT JOIN clients c ON c.id = s.client_id
            WHERE a.status = 'ACTIVE'
              AND a.start_date <= ?
              AND (a.end_date IS NULL OR a.end_date = '' OR a.end_date >= ?)
            """,
            (today, today),
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def _active_assignment_counts(today: str) -> dict[int, int]:
    conn = _db_connect()
    try:
        if not _table_exists(conn, "assignments"):
            return {}
        cur = conn.execute(
            """
            SELECT site_id, COUNT(*) AS total
            FROM assignments
            WHERE status = 'ACTIVE'
              AND start_date <= ?
              AND (end_date IS NULL OR end_date = '' OR end_date >= ?)
            GROUP BY site_id
            """,
            (today, today),
        )
        return {int(row["site_id"]): int(row["total"]) for row in cur.fetchall()}
    finally:
        conn.close()


def _attendance_checkins_for_date(
    today: str, email_to_user_id: dict[str, int]
) -> dict[int, int]:
    checkins: dict[int, int] = {}
    conn = _db_connect()
    try:
        if _table_exists(conn, "attendance"):
            cur = conn.execute(
                """
                SELECT employee_id, employee_email, time, action, created_at
                FROM attendance
                WHERE date = ? AND action = 'checkin'
                """,
                (today,),
            )
            for row in cur.fetchall():
                user_id = int(row["employee_id"]) if row["employee_id"] else None
                if not user_id and row["employee_email"]:
                    user_id = email_to_user_id.get(row["employee_email"])
                if not user_id:
                    continue
                minutes = _extract_minutes(row["time"], row["created_at"])
                if minutes is None:
                    continue
                current = checkins.get(user_id)
                if current is None or minutes < current:
                    checkins[user_id] = minutes
    finally:
        conn.close()
    return checkins


def _is_late_checkin(checkin_minutes: int | None, assignment: dict) -> bool:
    if checkin_minutes is None:
        return False
    policy = _resolve_attendance_policy(
        assignment.get("site_id"),
        assignment.get("client_id"),
        assignment.get("shift_id"),
    )
    cutoff_minutes = _parse_hhmm(policy.get("cutoff_time"))
    # Default start time when policy doesn't define a cutoff.
    start_minutes = cutoff_minutes if cutoff_minutes is not None else 9 * 60
    grace_minutes = int(policy.get("grace_minutes") or 0)
    late_threshold = int(policy.get("late_threshold_minutes") or 0)
    allowed_minutes = start_minutes + max(grace_minutes, late_threshold)
    return checkin_minutes > allowed_minutes


def _attendance_month_summary_for_employee(
    employee_email: str | None,
    assignment: dict | None,
    year_month: str | None = None,
) -> dict:
    summary = {"present": 0, "late": 0, "izin": 0, "sakit": 0}
    if not employee_email:
        return summary
    email_key = employee_email.strip().lower()
    if not email_key:
        return summary
    month_start, month_end = _month_bounds(year_month)
    start_key = month_start.strftime("%Y-%m-%d")
    end_key = month_end.strftime("%Y-%m-%d")
    conn = _db_connect()
    try:
        cur = conn.execute(
            """
            SELECT date, time, created_at
            FROM attendance
            WHERE lower(employee_email) = ? AND date BETWEEN ? AND ? AND action = 'checkin'
            """,
            (email_key, start_key, end_key),
        )
        earliest: dict[str, int] = {}
        for row in cur.fetchall():
            date_value = row["date"] or ""
            minutes = _extract_minutes(row["time"], row["created_at"])
            if minutes is None:
                continue
            current = earliest.get(date_value)
            if current is None or minutes < current:
                earliest[date_value] = minutes
        summary["present"] = len(earliest)
        if assignment:
            late = 0
            for minutes in earliest.values():
                if _is_late_checkin(minutes, assignment):
                    late += 1
            summary["late"] = late
        leave_counts = {"izin": 0, "sakit": 0}
        leave_cur = conn.execute(
            """
            SELECT leave_type, date_from, date_to, status
            FROM leave_requests
            WHERE lower(employee_email) = ? AND status = 'approved'
            """,
            (email_key,),
        )
        for row in leave_cur.fetchall():
            leave_type = (row["leave_type"] or "").lower()
            if leave_type not in leave_counts:
                continue
            start = _date_from_input(row["date_from"])
            end = _date_from_input(row["date_to"]) or start
            counted = _count_overlap_days(start, end, month_start, month_end)
            if counted:
                leave_counts[leave_type] += counted
        summary["izin"] = leave_counts["izin"]
        summary["sakit"] = leave_counts["sakit"]
    finally:
        conn.close()
    return summary


def _attendance_month_summary_for_user(user: User | None, year_month: str | None = None) -> dict:
    if not user:
        return {"present": 0, "late": 0, "izin": 0, "sakit": 0}
    assignment = _get_active_assignment(user.id)
    return _attendance_month_summary_for_employee(user.email, assignment, year_month)


def _client_operational_summary(
    today: str, user: User | None, clients: list[dict] | None = None
) -> list[dict]:
    start = time.perf_counter()
    clients = clients or _clients()
    if not clients:
        return []
    assignments = _list_active_assignments(today)
    assignment_by_employee: dict[int, dict] = {}
    email_to_user_id: dict[str, int] = {}
    client_employees: dict[int, set[int]] = {}
    for row in assignments:
        user_id = int(row["employee_user_id"])
        assignment_by_employee.setdefault(user_id, row)
        email = (_row_get(row, "employee_email") or "").lower()
        if email:
            email_to_user_id[email] = user_id
        client_id = _row_get(row, "client_id")
        if client_id is None:
            continue
        client_employees.setdefault(int(client_id), set()).add(user_id)

    checkins = _attendance_checkins_for_date(today, email_to_user_id)
    leave_pending_by_client: dict[int, int] = {}
    leave_excused_today: set[int] = set()
    pending_leaves = _list_leave_pending(user)
    active_leaves = _list_leave_active_for_date(today)
    for leave in pending_leaves:
        email = (leave.get("employee_email") or "").lower()
        if not email:
            continue
        user_id = email_to_user_id.get(email)
        if not user_id:
            user_row = _get_user_by_email(email)
            user_id = int(user_row["id"]) if user_row else None
        if not user_id:
            continue
        assignment = assignment_by_employee.get(user_id)
        if not assignment:
            continue
        client_id = assignment.get("client_id")
        if client_id is None:
            continue
        client_id = int(client_id)
        leave_pending_by_client[client_id] = leave_pending_by_client.get(client_id, 0) + 1

    for leave in active_leaves:
        email = (leave.get("employee_email") or "").lower()
        if not email:
            continue
        user_id = email_to_user_id.get(email)
        if not user_id:
            user_row = _get_user_by_email(email)
            user_id = int(user_row["id"]) if user_row else None
        if not user_id:
            continue
        leave_excused_today.add(user_id)

    summaries: list[dict] = []
    for client in clients:
        client_id = int(client.get("id"))
        employees = client_employees.get(client_id, set())
        late_count = 0
        absent_count = 0
        for user_id in employees:
            if user_id in checkins:
                assignment = assignment_by_employee.get(user_id)
                if assignment and _is_late_checkin(checkins[user_id], assignment):
                    late_count += 1
            else:
                if user_id not in leave_excused_today:
                    absent_count += 1
        summaries.append(
            {
                "client_id": client_id,
                "client_name": client.get("name") or "-",
                "late_count": late_count,
                "absent_count": absent_count,
                "leave_pending_count": leave_pending_by_client.get(client_id, 0),
            }
        )
    _perf_log(
        "client_operational_summary",
        start,
        f"clients={len(clients)} assignments={len(assignments)} pending={len(pending_leaves)}",
    )
    return summaries


def _client_leave_breakdown(today: str, emails: set[str]) -> dict[str, int]:
    counts = {"sakit": 0, "izin": 0}
    if not emails:
        return counts
    conn = _db_connect()
    try:
        if not _table_exists(conn, "leave_requests"):
            return counts
        placeholders = ",".join("?" for _ in emails)
        query = f"""
            SELECT lower(leave_type) AS leave_type, COUNT(1) AS total
            FROM leave_requests
            WHERE lower(employee_email) IN ({placeholders})
              AND status = 'approved'
              AND date_from <= ?
              AND date_to >= ?
            GROUP BY lower(leave_type)
        """
        params = [*sorted(emails), today, today]
        cur = conn.execute(query, params)
        for row in cur.fetchall():
            leave_type = (row["leave_type"] or "").lower()
            if leave_type in counts:
                counts[leave_type] = int(row["total"] or 0)
        return counts
    finally:
        conn.close()


def _leave_pending_count_for_emails(emails: set[str]) -> int:
    if not emails:
        return 0
    conn = _db_connect()
    try:
        if not _table_exists(conn, "leave_requests"):
            return 0
        placeholders = ",".join("?" for _ in emails)
        query = f"""
            SELECT COUNT(1) AS total
            FROM leave_requests
            WHERE status = 'pending'
              AND lower(employee_email) IN ({placeholders})
        """
        params = [*sorted({email.lower() for email in emails if email})]
        row = conn.execute(query, params).fetchone()
        return int(row["total"] or 0) if row else 0
    finally:
        conn.close()


def _site_operational_summary(today: str, site_id: int) -> dict[str, int]:
    assignments = [
        row
        for row in _list_active_assignments(today)
        if int(row.get("site_id") or 0) == site_id
    ]
    if not assignments:
        return {"late_count": 0, "absent_count": 0}
    assignment_by_employee: dict[int, dict] = {}
    email_to_user_id: dict[str, int] = {}
    for row in assignments:
        user_id = int(row.get("employee_user_id") or 0)
        if not user_id:
            continue
        assignment_by_employee[user_id] = row
        email = (row.get("employee_email") or "").lower()
        if email:
            email_to_user_id[email] = user_id
    checkins = _attendance_checkins_for_date(today, email_to_user_id)
    leave_excused_today: set[int] = set()
    active_leaves = _list_leave_active_for_date(today)
    for leave in active_leaves:
        email = (leave.get("employee_email") or "").lower()
        if not email:
            continue
        user_id = email_to_user_id.get(email)
        if not user_id:
            user_row = _get_user_by_email(email)
            user_id = int(user_row["id"]) if user_row else None
        if not user_id:
            continue
        leave_excused_today.add(user_id)
    late_count = 0
    absent_count = 0
    for user_id, assignment in assignment_by_employee.items():
        if user_id in checkins:
            if _is_late_checkin(checkins[user_id], assignment):
                late_count += 1
        else:
            if user_id not in leave_excused_today:
                absent_count += 1
    return {"late_count": late_count, "absent_count": absent_count}


def _policies_for_site(client_id: int, site_id: int) -> list[dict]:
    policies = _list_policies_by_client(client_id)
    scoped = []
    for policy in policies:
        scope_type = (policy.get("scope_type") or "").upper()
        if scope_type == "SITE" and int(policy.get("site_id") or 0) == site_id:
            scoped.append(policy)
    return scoped


def _client_users_for_site(client_id: int, site_id: int) -> list[dict]:
    return [
        u
        for u in _list_users()
        if u.get("role") in CLIENT_ROLES
        and int(u.get("client_id") or 0) == client_id
        and int(u.get("site_id") or 0) == site_id
    ]


def _ensure_client_superadmin_user(
    email: str, client_id: int, site_id: int
) -> tuple[bool, str]:
    if not _looks_like_email(email):
        return False, "Email PIC tidak valid."
    normalized = email.strip().lower()
    existing = _get_user_by_email(normalized)
    if existing:
        if existing["role"] != "client_admin":
            return False, "Email PIC sudah dipakai role lain."
        existing_client = int(_row_get(existing, "client_id") or 0)
        existing_site = int(_row_get(existing, "site_id") or 0)
        if existing_client and existing_client != client_id:
            return False, "Email PIC sudah terikat client lain."
        if existing_site and existing_site != site_id:
            return False, "Email PIC sudah terikat site lain."
        if not existing_client or not existing_site:
            _update_user_basic(
                user_id=int(existing["id"]),
                name=existing["name"] or "",
                role=existing["role"],
                is_active=int(existing["is_active"] or 1),
                client_id=client_id,
                update_client_id=True,
                site_id=site_id,
                update_site_id=True,
            )
        return True, "User client superadmin sudah terdaftar."
    _create_user(
        name=normalized.split("@")[0],
        email=normalized,
        role="client_admin",
        password=DEFAULT_CLIENT_PASSWORD,
        client_id=client_id,
        site_id=site_id,
        must_change_password=1,
    )
    return True, "User client superadmin dibuat."


def _active_policy_sets(today: str) -> tuple[set[int], set[int]]:
    policies = _list_policies()
    site_policy_ids: set[int] = set()
    client_policy_ids: set[int] = set()
    for policy in policies:
        if not _policy_active_for_date(policy, today):
            continue
        if policy.get("scope_type") == "SITE" and policy.get("site_id"):
            site_policy_ids.add(int(policy["site_id"]))
        if policy.get("scope_type") == "CLIENT" and policy.get("client_id"):
            client_policy_ids.add(int(policy["client_id"]))
    return site_policy_ids, client_policy_ids


def _active_policy_sets_for_client(today: str, client_id: int) -> tuple[set[int], set[int]]:
    policies = _list_policies_by_client(client_id)
    site_policy_ids: set[int] = set()
    client_policy_ids: set[int] = set()
    for policy in policies:
        if not _policy_active_for_date(policy, today):
            continue
        if policy.get("scope_type") == "SITE" and policy.get("site_id"):
            site_policy_ids.add(int(policy["site_id"]))
        if policy.get("scope_type") == "CLIENT" and policy.get("client_id"):
            client_policy_ids.add(int(policy["client_id"]))
    return site_policy_ids, client_policy_ids


def _get_policy_by_id(policy_id: int) -> dict | None:
    conn = _db_connect()
    try:
        if not _table_exists(conn, "attendance_policies"):
            return None
        cur = conn.execute("SELECT * FROM attendance_policies WHERE id = ?", (policy_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def _list_expired_assignments(today: str) -> list[dict]:
    conn = _db_connect()
    try:
        if not _table_exists(conn, "assignments"):
            return []
        cur = conn.execute(
            """
            SELECT
                a.id,
                a.employee_user_id,
                u.name AS employee_name,
                u.email AS employee_email,
                a.site_id,
                s.client_id,
                s.name AS site_name,
                COALESCE(c.name, s.client_name) AS client_name,
                a.end_date
            FROM assignments a
            JOIN users u ON u.id = a.employee_user_id
            JOIN sites s ON s.id = a.site_id
            LEFT JOIN clients c ON c.id = s.client_id
            WHERE a.status = 'ACTIVE'
              AND a.end_date IS NOT NULL
              AND a.end_date != ''
              AND a.end_date < ?
            ORDER BY a.end_date DESC
            """,
            (today,),
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def _alert_badge_class(count: int) -> str:
    if count <= 0:
        return "approved"
    if count <= 3:
        return "pending"
    return "rejected"


def _limit_alert_items(items: list[str], max_items: int = 6) -> dict:
    return {
        "items": items[:max_items],
        "extra": max(0, len(items) - max_items),
    }


def _build_admin_alerts(today: str, client_id: int | None = None) -> dict:
    if client_id:
        site_policy_ids, client_policy_ids = _active_policy_sets_for_client(today, client_id)
        sites = _list_sites_by_client(client_id)
    else:
        site_policy_ids, client_policy_ids = _active_policy_sets(today)
        sites = _list_sites()
    sites_without_policy = []
    for site in sites:
        site_id = int(site.get("id") or 0)
        site_client_id = site.get("client_id")
        has_policy = False
        if site_id and site_id in site_policy_ids:
            has_policy = True
        elif site_client_id and int(site_client_id) in client_policy_ids:
            has_policy = True
        if not has_policy:
            client_label = site.get("client_name") or "-"
            sites_without_policy.append(f"{client_label} - {site.get('name') or '-'}")

    employees_without_assignment = []
    if not client_id:
        employee_users = [
            e for e in _list_employee_users() if int(e.get("is_active") or 0) == 1
        ]
        active_assignments = _list_active_assignments(today)
        active_user_ids = {int(a.get("employee_user_id") or 0) for a in active_assignments}
        for employee in employee_users:
            user_id = int(employee.get("id") or 0)
            if user_id and user_id not in active_user_ids:
                label = employee.get("name") or employee.get("email") or "-"
                employees_without_assignment.append(label)

    expired_assignments = _list_expired_assignments(today)
    expired_labels = []
    for row in expired_assignments:
        if client_id and int(_row_get(row, "client_id") or 0) != client_id:
            continue
        name = _row_get(row, "employee_name") or _row_get(row, "employee_email") or "-"
        client = _row_get(row, "client_name") or "-"
        site = _row_get(row, "site_name") or "-"
        end_date = _row_get(row, "end_date") or "-"
        expired_labels.append(f"{name} - {client}/{site} (end: {end_date})")

    alerts = {
        "sites_without_policy": {
            "count": len(sites_without_policy),
            "badge_class": _alert_badge_class(len(sites_without_policy)),
            **_limit_alert_items(sites_without_policy),
        },
        "employees_without_assignment": {
            "count": len(employees_without_assignment),
            "badge_class": _alert_badge_class(len(employees_without_assignment)),
            **_limit_alert_items(employees_without_assignment),
        },
        "assignments_expired": {
            "count": len(expired_labels),
            "badge_class": _alert_badge_class(len(expired_labels)),
            **_limit_alert_items(expired_labels),
        },
    }
    return alerts


def _log_audit_event(
    entity_type: str,
    entity_id: int | None,
    action: str,
    actor: User | None,
    summary: str,
    details: dict | None = None,
) -> None:
    if not actor:
        return
    conn = _db_connect()
    try:
        if not _table_exists(conn, "audit_logs"):
            return
        conn.execute(
            """
            INSERT INTO audit_logs (
                entity_type, entity_id, action,
                actor_email, actor_role, summary, details_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entity_type,
                entity_id,
                action,
                actor.email,
                actor.role,
                summary,
                json.dumps(details or {}, ensure_ascii=True),
                _now_ts(),
            ),
        )
    finally:
        conn.commit()
        conn.close()


def _fetch_audit_logs(limit: int = 50) -> list[dict]:
    conn = _db_connect()
    try:
        if not _table_exists(conn, "audit_logs"):
            return []
        cur = conn.execute(
            """
            SELECT *
            FROM audit_logs
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def _validate_upload(file_obj, max_size: int) -> None:
    if not file_obj or not file_obj.filename:
        raise ValueError("File wajib diunggah.")
    mime = (file_obj.mimetype or "").lower()
    if not mime.startswith("image/"):
        raise ValueError("File harus berupa gambar.")
    try:
        file_obj.stream.seek(0, os.SEEK_END)
        size = file_obj.stream.tell()
        file_obj.stream.seek(0)
    except Exception:
        size = 0
    if size and size > max_size:
        raise ValueError("Ukuran file maksimal 10MB.")


def _save_upload(file_obj, subdir: str, max_size: int) -> str:
    _validate_upload(file_obj, max_size)
    safe_name = secure_filename(file_obj.filename) or "upload.jpg"
    ts = datetime.now().strftime("%Y%m%d%H%M%S%f")
    filename = f"{ts}_{safe_name}"
    base_dir = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.join(base_dir, "static", subdir)
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, filename)
    file_obj.save(file_path)
    return f"{subdir}/{filename}"


def _validate_leave_attachment(file_obj, max_size: int) -> None:
    if not file_obj or not file_obj.filename:
        raise ValueError("Lampiran wajib diunggah.")
    mime = (file_obj.mimetype or "").lower()
    if not (mime.startswith("image/") or mime == "application/pdf"):
        raise ValueError("Lampiran harus berupa gambar atau PDF.")
    try:
        file_obj.stream.seek(0, os.SEEK_END)
        size = file_obj.stream.tell()
        file_obj.stream.seek(0)
    except Exception:
        size = 0
    if size and size > max_size:
        raise ValueError("Ukuran lampiran maksimal 2MB.")


def _save_leave_attachment(file_obj, subdir: str, max_size: int) -> str:
    _validate_leave_attachment(file_obj, max_size)
    safe_name = secure_filename(file_obj.filename) or "attachment"
    ts = datetime.now().strftime("%Y%m%d%H%M%S%f")
    filename = f"{ts}_{safe_name}"
    base_dir = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.join(base_dir, "static", subdir)
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, filename)
    file_obj.save(file_path)
    return f"{subdir}/{filename}"


def _decode_base64_payload(data: str) -> tuple[str | None, bytes]:
    if not data:
        raise ValueError("Lampiran tidak valid.")
    payload = data.strip()
    if payload.startswith("data:") and "," in payload:
        header, body = payload.split(",", 1)
        mime = header[5:].split(";")[0].strip()
    else:
        mime = None
        body = payload
    try:
        decoded = base64.b64decode(body, validate=True)
    except Exception:
        raise ValueError("Lampiran tidak valid.")
    return mime, decoded


def _extension_from_mime(mime: str | None) -> str:
    if not mime:
        return ".bin"
    if mime == "application/pdf":
        return ".pdf"
    if mime == "image/jpeg":
        return ".jpg"
    if mime == "image/png":
        return ".png"
    if mime == "image/gif":
        return ".gif"
    if mime.startswith("image/"):
        return ".jpg"
    return ".bin"


def _save_base64_attachment(data: str, subdir: str, max_size: int) -> str:
    mime, decoded = _decode_base64_payload(data)
    if mime and not (mime.startswith("image/") or mime == "application/pdf"):
        raise ValueError("Lampiran harus berupa gambar atau PDF.")
    if len(decoded) > max_size:
        raise ValueError("Ukuran lampiran maksimal 2MB.")
    ts = datetime.now().strftime("%Y%m%d%H%M%S%f")
    ext = _extension_from_mime(mime)
    filename = f"{ts}_attachment{ext}"
    base_dir = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.join(base_dir, "static", subdir)
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, filename)
    with open(file_path, "wb") as handle:
        handle.write(decoded)
    return f"{subdir}/{filename}"


def _row_get(row: sqlite3.Row | dict | None, key: str, default: any = None) -> any:
    """
    Safely get value from sqlite3.Row or dict without using .get() method.
    sqlite3.Row doesn't have .get() method, only bracket notation [].
    """
    if row is None:
        return default
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return default


def _db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _user_row_to_user(row: sqlite3.Row, theme: str) -> User:
    return User(
        id=int(row["id"]),
        email=row["email"],
        role=row["role"],
        name=row["name"] or "",
        theme=theme,
        selfie_path=row["selfie_path"] if "selfie_path" in row.keys() else None,
        must_change_password=int(row["must_change_password"] or 0),
        client_id=int(row["client_id"]) if "client_id" in row.keys() and row["client_id"] is not None else None,
        site_id=int(row["site_id"]) if "site_id" in row.keys() and row["site_id"] is not None else None,
    )


def _get_user_by_email(email: str) -> sqlite3.Row | None:
    conn = _db_connect()
    try:
        cur = conn.execute("SELECT * FROM users WHERE email = ?", (email.lower(),))
        return cur.fetchone()
    finally:
        conn.close()


def _get_user_by_id(user_id: int) -> sqlite3.Row | None:
    conn = _db_connect()
    try:
        cur = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cur.fetchone()
    finally:
        conn.close()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _generate_otp_token() -> str:
    return f"{secrets.randbelow(1000000):06d}"


def _create_password_reset_token(
    user_id: int,
    token: str | None = None,
    ttl_minutes: int = 30,
) -> str:
    token = token or secrets.token_urlsafe(32)
    token_hash = _hash_token(token)
    expires_at = (datetime.now() + timedelta(minutes=ttl_minutes)).strftime("%Y-%m-%d %H:%M:%S")
    conn = _db_connect()
    try:
        conn.execute(
            "DELETE FROM password_reset_tokens WHERE user_id = ? AND used_at IS NULL",
            (user_id,),
        )
        conn.execute(
            """
            INSERT INTO password_reset_tokens (
                user_id, token_hash, expires_at, created_at, used_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, token_hash, expires_at, _now_ts(), None),
        )
    finally:
        conn.commit()
        conn.close()
    return token


def _consume_password_reset_token(token: str) -> int | None:
    token_hash = _hash_token(token)
    now_ts = _now_ts()
    conn = _db_connect()
    try:
        row = conn.execute(
            """
            SELECT id, user_id, expires_at
            FROM password_reset_tokens
            WHERE token_hash = ? AND used_at IS NULL
            LIMIT 1
            """,
            (token_hash,),
        ).fetchone()
        if not row:
            return None
        if row["expires_at"] < now_ts:
            return None
        conn.execute(
            "UPDATE password_reset_tokens SET used_at = ? WHERE id = ?",
            (now_ts, row["id"]),
        )
        return int(row["user_id"])
    finally:
        conn.commit()
        conn.close()


def _get_client_by_id(client_id: int | None) -> sqlite3.Row | None:
    if not client_id:
        return None
    conn = _db_connect()
    try:
        cur = conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
        return cur.fetchone()
    finally:
        conn.close()


def _get_site_by_id(site_id: int | None) -> sqlite3.Row | None:
    if not site_id:
        return None
    conn = _db_connect()
    try:
        cur = conn.execute("SELECT * FROM sites WHERE id = ?", (site_id,))
        return cur.fetchone()
    finally:
        conn.close()


def _get_active_assignment(user_id: int) -> dict | None:
    conn = _db_connect()
    try:
        if not _table_exists(conn, "assignments"):
            return None
        cur = conn.execute(
            """
            SELECT *
            FROM assignments
            WHERE employee_user_id = ?
              AND status = 'ACTIVE'
            ORDER BY start_date DESC, created_at DESC, id DESC
            """,
            (user_id,),
        )
        rows = [dict(row) for row in cur.fetchall()]
        if not rows:
            return None
        today = datetime.fromisoformat(_today_key()).date()
        for row in rows:
            start_dt = _date_from_input(_row_get(row, "start_date"))
            if not start_dt:
                continue
            end_dt = _date_from_input(_row_get(row, "end_date")) if _row_get(row, "end_date") else None
            if start_dt <= today and (not end_dt or end_dt >= today):
                return row
            return rows[0]
    finally:
        conn.close()


def _get_shift_by_id(shift_id: int | None) -> sqlite3.Row | None:
    if not shift_id:
        return None
    conn = _db_connect()
    try:
        cur = conn.execute("SELECT * FROM shifts WHERE id = ?", (shift_id,))
        return cur.fetchone()
    finally:
        conn.close()


def _get_assignment_by_id(assignment_id: int) -> dict | None:
    conn = _db_connect()
    try:
        if not _table_exists(conn, "assignments"):
            return None
        cur = conn.execute("SELECT * FROM assignments WHERE id = ?", (assignment_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def _policy_with_defaults(row: sqlite3.Row | None) -> dict:
    policy = DEFAULT_ATTENDANCE_POLICY.copy()
    if not row:
        return policy
    for key in policy.keys():
        if key in row.keys() and row[key] is not None:
            policy[key] = row[key]
    return policy


def _resolve_attendance_policy(
    site_id: int | None, client_id: int | None, shift_id: int | None
) -> dict:
    conn = _db_connect()
    try:
        if not _table_exists(conn, "attendance_policies"):
            return DEFAULT_ATTENDANCE_POLICY.copy()
        today = _today_key()
        if site_id:
            if shift_id:
                cur = conn.execute(
                    """
                    SELECT *
                    FROM attendance_policies
                    WHERE scope_type = 'SITE'
                      AND site_id = ?
                      AND shift_id = ?
                      AND effective_from <= ?
                      AND (effective_to IS NULL OR effective_to = '' OR effective_to >= ?)
                    ORDER BY effective_from DESC
                    LIMIT 1
                    """,
                    (site_id, shift_id, today, today),
                )
                row = cur.fetchone()
                if row:
                    return _policy_with_defaults(row)
            cur = conn.execute(
                """
                SELECT *
                FROM attendance_policies
                WHERE scope_type = 'SITE'
                  AND site_id = ?
                  AND (shift_id IS NULL OR shift_id = '')
                  AND effective_from <= ?
                  AND (effective_to IS NULL OR effective_to = '' OR effective_to >= ?)
                ORDER BY effective_from DESC
                LIMIT 1
                """,
                (site_id, today, today),
            )
            row = cur.fetchone()
            if row:
                return _policy_with_defaults(row)
        if client_id:
            if shift_id:
                cur = conn.execute(
                    """
                    SELECT *
                    FROM attendance_policies
                    WHERE scope_type = 'CLIENT'
                      AND client_id = ?
                      AND shift_id = ?
                      AND effective_from <= ?
                      AND (effective_to IS NULL OR effective_to = '' OR effective_to >= ?)
                    ORDER BY effective_from DESC
                    LIMIT 1
                    """,
                    (client_id, shift_id, today, today),
                )
                row = cur.fetchone()
                if row:
                    return _policy_with_defaults(row)
            cur = conn.execute(
                """
                SELECT *
                FROM attendance_policies
                WHERE scope_type = 'CLIENT'
                  AND client_id = ?
                  AND (shift_id IS NULL OR shift_id = '')
                  AND effective_from <= ?
                  AND (effective_to IS NULL OR effective_to = '' OR effective_to >= ?)
                ORDER BY effective_from DESC
                LIMIT 1
                """,
                (client_id, today, today),
            )
            row = cur.fetchone()
            if row:
                return _policy_with_defaults(row)
        return DEFAULT_ATTENDANCE_POLICY.copy()
    finally:
        conn.close()


def _create_user(
    name: str,
    email: str,
    role: str,
    password: str,
    is_active: int = 1,
    must_change_password: int = 0,
    selfie_path: str | None = None,
    client_id: int | None = None,
    site_id: int | None = None,
) -> int:
    conn = _db_connect()
    try:
        cur = conn.execute(
            """
            INSERT INTO users (
                name, email, role, password_hash, is_active,
                created_at, updated_at, must_change_password, selfie_path, client_id, site_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                email.lower(),
                role,
                generate_password_hash(password),
                is_active,
                _now_ts(),
                _now_ts(),
                must_change_password,
                selfie_path,
                client_id,
                site_id,
            ),
        )
        return int(cur.lastrowid)
    finally:
        conn.commit()
        conn.close()


def _create_user_with_conn(
    conn: sqlite3.Connection,
    name: str,
    email: str,
    role: str,
    password: str,
    is_active: int = 1,
    must_change_password: int = 0,
    selfie_path: str | None = None,
    client_id: int | None = None,
    site_id: int | None = None,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO users (
            name, email, role, password_hash, is_active,
            created_at, updated_at, must_change_password, selfie_path, client_id, site_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            email.lower(),
            role,
            generate_password_hash(password),
            is_active,
            _now_ts(),
            _now_ts(),
            must_change_password,
            selfie_path,
            client_id,
            site_id,
        ),
    )
    return int(cur.lastrowid)


def _update_user_basic(
    user_id: int,
    name: str,
    role: str,
    is_active: int,
    email: str | None = None,
    client_id: int | None = None,
    update_client_id: bool = False,
    site_id: int | None = None,
    update_site_id: bool = False,
) -> None:
    conn = _db_connect()
    try:
        updates = ["name = ?", "role = ?", "is_active = ?", "updated_at = ?"]
        params: list = [name, role, is_active, _now_ts()]
        if email is not None:
            updates.insert(1, "email = ?")
            params.insert(1, email.lower())
        if update_client_id:
            updates.append("client_id = ?")
            params.append(client_id)
        if update_site_id:
            updates.append("site_id = ?")
            params.append(site_id)
        params.append(user_id)
        conn.execute(
            f"""
            UPDATE users
            SET {", ".join(updates)}
            WHERE id = ?
            """,
            tuple(params),
        )
    finally:
        conn.commit()
        conn.close()


def _update_user_password(user_id: int, password: str, must_change_password: int) -> None:
    conn = _db_connect()
    try:
        conn.execute(
            """
            UPDATE users
            SET password_hash = ?, must_change_password = ?, updated_at = ?
            WHERE id = ?
            """,
            (generate_password_hash(password), must_change_password, _now_ts(), user_id),
        )
    finally:
        conn.commit()
        conn.close()


def _update_user_selfie_path(user_id: int, selfie_path: str | None) -> None:
    conn = _db_connect()
    try:
        conn.execute(
            """
            UPDATE users
            SET selfie_path = ?, updated_at = ?
            WHERE id = ?
            """,
            (selfie_path, _now_ts(), user_id),
        )
    finally:
        conn.commit()
        conn.close()


def _update_user_selfie_path_with_conn(
    conn: sqlite3.Connection, user_id: int, selfie_path: str | None
) -> None:
    conn.execute(
        """
        UPDATE users
        SET selfie_path = ?, updated_at = ?
        WHERE id = ?
        """,
        (selfie_path, _now_ts(), user_id),
    )


def _delete_uploaded_file(path: str) -> None:
    if not path:
        return
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "static", path)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except OSError:
        pass


def _delete_user(user_id: int) -> None:
    conn = _db_connect()
    try:
        conn.execute("DELETE FROM supervisor_sites WHERE supervisor_user_id = ?", (user_id,))
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    finally:
        conn.commit()
        conn.close()


def _list_users() -> list[dict]:
    conn = _db_connect()
    try:
        cur = conn.execute(
            """
            SELECT
                u.id,
                u.name,
                u.email,
                u.role,
                u.is_active,
                u.created_at,
                u.must_change_password,
                u.client_id,
                u.site_id,
                c.name AS client_name,
                s.name AS site_name
            FROM users u
            LEFT JOIN clients c ON c.id = u.client_id
            LEFT JOIN sites s ON s.id = u.site_id
            ORDER BY u.created_at DESC
            """
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def _active_hr_superadmin_count(exclude_user_id: int | None = None) -> int:
    conn = _db_connect()
    try:
        if exclude_user_id:
            cur = conn.execute(
                """
                SELECT COUNT(*) AS total
                FROM users
                WHERE role = 'hr_superadmin' AND is_active = 1 AND id != ?
                """,
                (exclude_user_id,),
            )
        else:
            cur = conn.execute(
                "SELECT COUNT(*) AS total FROM users WHERE role = 'hr_superadmin' AND is_active = 1"
            )
        row = cur.fetchone()
        return int(row["total"] if row else 0)
    finally:
        conn.close()


def _list_clients() -> list[dict]:
    conn = _db_connect()
    try:
        if not _table_exists(conn, "clients"):
            return []
        cur = conn.execute(
            """
            SELECT
                id, name, legal_name, address, office_email, office_phone,
                pic_name, pic_title, pic_phone, is_active, notes, created_at
            FROM clients
            ORDER BY created_at DESC
            """
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def _list_employees(
    query: str | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> list[dict]:
    start = time.perf_counter()
    if limit is None and ADMIN_LIST_LIMIT > 0:
        limit = ADMIN_LIST_LIMIT
    conn = _db_connect()
    try:
        if not _table_exists(conn, "employees"):
            return []
        base_query = """
            SELECT
                id, nik, name, email, no_hp, address,
                gender, status_nikah, notes, is_active, created_at, site_id
            FROM employees
        """
        clauses = []
        params: list = []
        if query:
            like = f"%{query.strip().lower()}%"
            clauses.append("(lower(name) LIKE ? OR lower(email) LIKE ? OR no_hp LIKE ?)")
            params.extend([like, like, like])
        if clauses:
            base_query += " WHERE " + " AND ".join(clauses)
        base_query += " ORDER BY created_at DESC"
        if limit:
            base_query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        cur = conn.execute(base_query, tuple(params))
        rows = [dict(row) for row in cur.fetchall()]
        for row in rows:
            row.setdefault("client", "-")
        _perf_log("list_employees", start, f"rows={len(rows)}")
        return rows
    finally:
        conn.close()


def _list_employees_by_site(site_id: int) -> list[dict]:
    conn = _db_connect()
    try:
        if _table_exists(conn, "assignments") and _table_exists(conn, "users"):
            today = _today_key()
            cur = conn.execute(
                """
                SELECT DISTINCT
                    COALESCE(e.id, u.id) AS id,
                    e.nik,
                    COALESCE(e.name, u.name) AS name,
                    COALESCE(e.email, u.email) AS email,
                    e.no_hp,
                    e.address,
                    e.gender,
                    e.status_nikah,
                    e.notes,
                    COALESCE(e.is_active, u.is_active, 1) AS is_active,
                    e.created_at,
                    a.site_id
                FROM assignments a
                JOIN users u ON u.id = a.employee_user_id
                LEFT JOIN employees e ON lower(e.email) = lower(u.email)
                WHERE a.site_id = ?
                  AND a.status = 'ACTIVE'
                  AND a.start_date <= ?
                  AND (a.end_date IS NULL OR a.end_date = '' OR a.end_date >= ?)
                ORDER BY COALESCE(e.created_at, a.created_at) DESC
                """,
                (site_id, today, today),
            )
            return [dict(row) for row in cur.fetchall()]
        if not _table_exists(conn, "employees"):
            return []
        cur = conn.execute(
            """
            SELECT
                id, nik, name, email, no_hp, address,
                gender, status_nikah, notes, is_active, created_at, site_id
            FROM employees
            WHERE site_id = ?
            ORDER BY created_at DESC
            """,
            (site_id,),
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def _create_employee(
    nik: str,
    name: str,
    email: str,
    no_hp: str,
    address: str,
    gender: str,
    status_nikah: str,
    notes: str | None,
    is_active: int = 1,
    site_id: int | None = None,
) -> None:
    conn = _db_connect()
    try:
        conn.execute(
            """
            INSERT INTO employees (
                nik, name, email, no_hp, address, gender,
                status_nikah, notes, is_active, created_at, site_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                nik,
                name,
                email,
                no_hp,
                address,
                gender,
                status_nikah,
                notes or None,
                is_active,
                _now_ts(),
                site_id,
            ),
        )
    finally:
        conn.commit()
        conn.close()


def _parse_employee_form(form: dict) -> tuple[dict, str | None]:
    nik = (form.get("nik") or "").strip()
    name = (form.get("name") or "").strip()
    email = (form.get("email") or "").strip().lower()
    no_hp = (form.get("no_hp") or "").strip()
    address = (form.get("address") or "").strip()
    gender = (form.get("gender") or "").strip()
    status_nikah = (form.get("status_nikah") or "").strip()
    notes = (form.get("notes") or "").strip()
    if not nik:
        return {}, "NIK wajib diisi."
    if not name:
        return {}, "Nama wajib diisi."
    if not email:
        return {}, "Email wajib diisi."
    if not _looks_like_email(email):
        return {}, "Email tidak valid."
    if not no_hp:
        return {}, "No HP wajib diisi."
    if not address:
        return {}, "Alamat wajib diisi."
    if not gender:
        return {}, "Jenis kelamin wajib dipilih."
    if not status_nikah:
        return {}, "Status nikah wajib dipilih."
    return {
        "nik": nik,
        "name": name,
        "email": email,
        "no_hp": no_hp,
        "address": address,
        "gender": gender,
        "status_nikah": status_nikah,
        "notes": notes or None,
    }, None


def _parse_assignment_payload(form: dict) -> tuple[dict | None, str | None]:
    start_date_raw = (form.get("start_date") or "").strip()
    if not start_date_raw:
        return None, "Tanggal mulai assignment wajib diisi."
    normalized_start = _normalize_date_input(start_date_raw)
    if not normalized_start:
        return None, "Tanggal mulai assignment wajib format DD-MM-YYYY (contoh 01-02-2026) atau 1 Feb 2026."
    end_date_raw = (form.get("end_date") or "").strip()
    normalized_end = None
    if end_date_raw:
        normalized_end = _normalize_date_input(end_date_raw)
        if not normalized_end:
            return None, "Tanggal selesai assignment wajib format DD-MM-YYYY (contoh 01-02-2026) atau 1 Feb 2026."
    use_shift = (form.get("use_shift") or "").strip() == "1"
    shift_id = None
    shift_id_raw = (form.get("shift_id") or "").strip()
    if use_shift and shift_id_raw:
        if not shift_id_raw.isdigit():
            return None, "Shift tidak valid."
        shift_id = int(shift_id_raw)
    job_title = (form.get("job_title") or "").strip() or None
    status = (form.get("status") or "ACTIVE").strip().upper()
    if status not in {"ACTIVE", "ENDED"}:
        status = "ACTIVE"
    return {
        "shift_id": shift_id,
        "job_title": job_title,
        "start_date": normalized_start,
        "end_date": normalized_end,
        "status": status,
    }, None


def _set_employee_active_with_conn(conn: sqlite3.Connection, email: str, is_active: int) -> None:
    conn.execute(
        "UPDATE employees SET is_active = ? WHERE LOWER(email) = ?",
        (is_active, email.lower()),
    )


def _update_employee(
    employee_id: int,
    nik: str,
    name: str,
    email: str,
    no_hp: str,
    address: str,
    gender: str,
    status_nikah: str,
    notes: str | None,
    is_active: int,
) -> None:
    conn = _db_connect()
    try:
        conn.execute(
            """
            UPDATE employees
            SET
                nik = ?, name = ?, email = ?, no_hp = ?, address = ?,
                gender = ?, status_nikah = ?, notes = ?, is_active = ?
            WHERE id = ?
            """,
            (
                nik,
                name,
                email,
                no_hp,
                address,
                gender,
                status_nikah,
                notes or None,
                is_active,
                employee_id,
            ),
        )
    finally:
        conn.commit()
        conn.close()


def _delete_employee(employee_id: int) -> None:
    conn = _db_connect()
    try:
        conn.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
    finally:
        conn.commit()
        conn.close()


def _delete_assignments_for_employee(employee_user_id: int, site_id: int | None = None) -> int:
    if not employee_user_id:
        return 0
    conn = _db_connect()
    try:
        if not _table_exists(conn, "assignments"):
            return 0
        if site_id:
            cur = conn.execute(
                "DELETE FROM assignments WHERE employee_user_id = ? AND site_id = ?",
                (employee_user_id, site_id),
            )
        else:
            cur = conn.execute(
                "DELETE FROM assignments WHERE employee_user_id = ?",
                (employee_user_id,),
            )
        return cur.rowcount or 0
    finally:
        conn.commit()
        conn.close()


def _list_employee_registration_codes(limit: int = 200) -> list[dict]:
    conn = _db_connect()
    try:
        if not _table_exists(conn, "employee_registration_codes"):
            return []
        cur = conn.execute(
            """
            SELECT id, year_month, seq, registrant_count, used_count, code, created_at
            FROM employee_registration_codes
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def _next_employee_registration_seq(year_month: str) -> int:
    conn = _db_connect()
    try:
        if not _table_exists(conn, "employee_registration_codes"):
            return 1
        cur = conn.execute(
            "SELECT MAX(seq) AS max_seq FROM employee_registration_codes WHERE year_month = ?",
            (year_month,),
        )
        row = cur.fetchone()
        return int(row["max_seq"] or 0) + 1
    finally:
        conn.close()


def _create_employee_registration_code(registrant_count: int) -> str:
    now = datetime.now()
    year_month = now.strftime("%Y%m")
    seq = _next_employee_registration_seq(year_month)
    code = f"{now.strftime('%y%m')}GMI-{seq:03d}{registrant_count:02d}"
    conn = _db_connect()
    try:
        conn.execute(
            """
            INSERT INTO employee_registration_codes (
                year_month, seq, registrant_count, used_count, code, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (year_month, seq, registrant_count, 0, code, _now_ts()),
        )
    finally:
        conn.commit()
        conn.close()
    return code


def _looks_like_employee_invite(code: str) -> bool:
    return bool(re.fullmatch(r"\d{4}GMI-\d{5}", code.strip(), flags=re.IGNORECASE))


def _consume_employee_registration_code(code: str) -> tuple[bool, str]:
    conn = _db_connect()
    normalized = code.strip().upper()
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            """
            SELECT id, registrant_count, COALESCE(used_count, 0) AS used_count
            FROM employee_registration_codes
            WHERE UPPER(code) = ?
            """,
            (normalized,),
        ).fetchone()
        if not row:
            conn.rollback()
            return False, "Kode undangan tidak dikenal."
        if int(row["used_count"] or 0) >= int(row["registrant_count"] or 0):
            conn.rollback()
            return False, "Kuota kode undangan sudah habis."
        conn.execute(
            """
            UPDATE employee_registration_codes
            SET used_count = COALESCE(used_count, 0) + 1
            WHERE id = ?
            """,
            (row["id"],),
        )
        conn.commit()
        return True, ""
    finally:
        conn.close()


def _consume_employee_registration_code_with_conn(
    conn: sqlite3.Connection, code: str
) -> tuple[bool, str]:
    normalized = code.strip().upper()
    row = conn.execute(
        """
        SELECT id, registrant_count, COALESCE(used_count, 0) AS used_count
        FROM employee_registration_codes
        WHERE UPPER(code) = ?
        """,
        (normalized,),
    ).fetchone()
    if not row:
        return False, "Kode undangan tidak dikenal."
    if int(row["used_count"] or 0) >= int(row["registrant_count"] or 0):
        return False, "Kuota kode undangan sudah habis."
    conn.execute(
        """
        UPDATE employee_registration_codes
        SET used_count = COALESCE(used_count, 0) + 1
        WHERE id = ?
        """,
        (row["id"],),
    )
    return True, ""


def _employee_by_email(email: str, only_active: bool = False) -> dict | None:
    if not email:
        return None
    conn = _db_connect()
    try:
        if not _table_exists(conn, "employees"):
            return None
        clause = "AND is_active = 1" if only_active else ""
        cur = conn.execute(
            f"""
            SELECT
                id, nik, name, email, no_hp, address,
                gender, status_nikah, notes, is_active, created_at
            FROM employees
            WHERE lower(email) = ? {clause}
            LIMIT 1
            """,
            (email.lower(),),
        )
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def _employee_by_phone(phone: str, only_active: bool = False) -> dict | None:
    normalized = _normalize_phone(phone)
    if not normalized:
        return None
    conn = _db_connect()
    try:
        if not _table_exists(conn, "employees"):
            return None
        clause = "WHERE is_active = 1" if only_active else ""
        cur = conn.execute(
            f"""
            SELECT
                id, nik, name, email, no_hp, address,
                gender, status_nikah, notes, is_active, created_at
            FROM employees
            {clause}
            """
        )
        rows = cur.fetchall()
        for row in rows:
            if _normalize_phone(row["no_hp"]) == normalized:
                return dict(row)
        return None
    finally:
        conn.close()


def _normalize_client_identity(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    return value if value else None


def _find_client_identity_conflict(
    name: str,
    legal_name: str | None,
    exclude_client_id: int | None = None,
) -> dict | None:
    identities: list[str] = []
    normalized_name = _normalize_client_identity(name)
    if normalized_name:
        identities.append(normalized_name.lower())
    normalized_legal = _normalize_client_identity(legal_name)
    if normalized_legal:
        identities.append(normalized_legal.lower())
    if not identities:
        return None
    conn = _db_connect()
    try:
        if not _table_exists(conn, "clients"):
            return None
        placeholders = ", ".join("?" for _ in identities)
        params = identities + identities
        query = f"""
            SELECT id, name, legal_name
            FROM clients
            WHERE lower(name) IN ({placeholders})
               OR lower(legal_name) IN ({placeholders})
        """
        if exclude_client_id is not None:
            query += " AND id != ?"
            params.append(exclude_client_id)
        cur = conn.execute(query, params)
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def _create_client(
    name: str,
    legal_name: str | None,
    address: str,
    office_email: str,
    office_phone: str,
    pic_name: str,
    pic_title: str,
    pic_phone: str,
    notes: str | None,
) -> None:
    conn = _db_connect()
    try:
        conn.execute(
            """
            INSERT INTO clients (
                name, legal_name, address, office_email, office_phone,
                pic_name, pic_title, pic_phone, is_active, notes, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                legal_name or None,
                address,
                office_email,
                office_phone,
                pic_name,
                pic_title,
                pic_phone,
                1,
                notes or None,
                _now_ts(),
            ),
        )
    finally:
        conn.commit()
        conn.close()


def _update_client(
    client_id: int,
    name: str,
    legal_name: str | None,
    address: str,
    office_email: str,
    office_phone: str,
    pic_name: str,
    pic_title: str,
    pic_phone: str,
    is_active: int,
    notes: str | None,
) -> None:
    conn = _db_connect()
    try:
        conn.execute(
            """
            UPDATE clients
            SET
                name = ?, legal_name = ?, address = ?, office_email = ?, office_phone = ?,
                pic_name = ?, pic_title = ?, pic_phone = ?,
                is_active = ?, notes = ?
            WHERE id = ?
            """,
            (
                name,
                legal_name or None,
                address,
                office_email,
                office_phone,
                pic_name,
                pic_title,
                pic_phone,
                is_active,
                notes or None,
                client_id,
            ),
        )
    finally:
        conn.commit()
        conn.close()


def _client_has_sites(client_id: int) -> bool:
    conn = _db_connect()
    try:
        cur = conn.execute(
            "SELECT 1 FROM sites WHERE client_id = ? LIMIT 1",
            (client_id,),
        )
        return cur.fetchone() is not None
    finally:
        conn.close()


def _delete_client(client_id: int) -> None:
    conn = _db_connect()
    try:
        conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))
    finally:
        conn.commit()
        conn.close()


def _delete_site(site_id: int) -> None:
    conn = _db_connect()
    try:
        conn.execute("DELETE FROM sites WHERE id = ?", (site_id,))
    finally:
        conn.commit()
        conn.close()


def _list_sites() -> list[dict]:
    conn = _db_connect()
    try:
        cur = conn.execute(
            """
            SELECT
                s.id,
                s.client_id,
                COALESCE(c.name, s.client_name) AS client_name,
                s.name,
                s.timezone,
                s.work_mode,
                s.latitude,
                s.longitude,
                s.radius_meters,
                s.notes,
                s.pic_name,
                s.pic_email,
                s.is_active,
                s.created_at,
                CASE
                    WHEN s.client_id IS NOT NULL AND c.id IS NULL THEN 1
                    ELSE 0
                END AS is_orphan
            FROM sites s
            LEFT JOIN clients c ON c.id = s.client_id
            ORDER BY s.created_at DESC
            """
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def _list_sites_by_client(client_id: int) -> list[dict]:
    conn = _db_connect()
    try:
        cur = conn.execute(
            """
            SELECT
                s.id,
                s.client_id,
                COALESCE(c.name, s.client_name) AS client_name,
                s.name,
                s.timezone,
                s.work_mode,
                s.latitude,
                s.longitude,
                s.radius_meters,
                s.notes,
                s.pic_name,
                s.pic_email,
                s.is_active,
                s.created_at
            FROM sites s
            LEFT JOIN clients c ON c.id = s.client_id
            WHERE s.client_id = ?
            ORDER BY s.created_at DESC
            """,
            (client_id,),
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def _list_client_contacts(client_id: int) -> list[dict]:
    conn = _db_connect()
    try:
        if not _table_exists(conn, "client_contacts"):
            return []
        cur = conn.execute(
            """
            SELECT
                id,
                client_id,
                contact_type,
                name,
                title,
                phone,
                email,
                is_primary,
                notes,
                created_at,
                updated_at
            FROM client_contacts
            WHERE client_id = ?
            ORDER BY is_primary DESC, created_at DESC
            """,
            (client_id,),
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def _get_client_contact_by_id(contact_id: int) -> dict | None:
    conn = _db_connect()
    try:
        if not _table_exists(conn, "client_contacts"):
            return None
        cur = conn.execute("SELECT * FROM client_contacts WHERE id = ?", (contact_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def _create_client_contact(
    client_id: int,
    contact_type: str,
    name: str,
    title: str | None,
    phone: str | None,
    email: str | None,
    is_primary: int,
    notes: str | None,
) -> None:
    conn = _db_connect()
    try:
        if is_primary:
            conn.execute(
                """
                UPDATE client_contacts
                SET is_primary = 0, updated_at = ?
                WHERE client_id = ? AND contact_type = ?
                """,
                (_now_ts(), client_id, contact_type),
            )
        conn.execute(
            """
            INSERT INTO client_contacts (
                client_id, contact_type, name, title, phone, email,
                is_primary, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                client_id,
                contact_type,
                name,
                title or None,
                phone or None,
                email or None,
                1 if is_primary else 0,
                notes or None,
                _now_ts(),
                _now_ts(),
            ),
        )
    finally:
        conn.commit()
        conn.close()


def _set_primary_client_contact(contact_id: int) -> None:
    conn = _db_connect()
    try:
        cur = conn.execute(
            "SELECT client_id, contact_type FROM client_contacts WHERE id = ?",
            (contact_id,),
        )
        row = cur.fetchone()
        if not row:
            return
        client_id = row["client_id"]
        contact_type = row["contact_type"]
        conn.execute(
            """
            UPDATE client_contacts
            SET is_primary = 0, updated_at = ?
            WHERE client_id = ? AND contact_type = ?
            """,
            (_now_ts(), client_id, contact_type),
        )
        conn.execute(
            """
            UPDATE client_contacts
            SET is_primary = 1, updated_at = ?
            WHERE id = ?
            """,
            (_now_ts(), contact_id),
        )
    finally:
        conn.commit()
        conn.close()


def _delete_client_contact(contact_id: int) -> None:
    conn = _db_connect()
    try:
        conn.execute("DELETE FROM client_contacts WHERE id = ?", (contact_id,))
    finally:
        conn.commit()
        conn.close()


def _list_employee_users() -> list[dict]:
    conn = _db_connect()
    try:
        cur = conn.execute(
            """
            SELECT id, name, email, is_active
            FROM users
            WHERE role = 'employee'
            ORDER BY name, email
            """
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def _list_assignments_by_client(client_id: int) -> list[dict]:
    conn = _db_connect()
    try:
        if not _table_exists(conn, "assignments"):
            return []
        cur = conn.execute(
            """
            SELECT
                a.id,
                a.employee_user_id,
                u.name AS employee_name,
                u.email AS employee_email,
                a.site_id,
                s.name AS site_name,
                COALESCE(c.name, s.client_name) AS client_name,
                a.shift_id,
                sh.name AS shift_name,
                a.job_title,
                a.start_date,
                a.end_date,
                a.status,
                a.created_at,
                a.updated_at
            FROM assignments a
            JOIN users u ON u.id = a.employee_user_id
            JOIN sites s ON s.id = a.site_id
            LEFT JOIN clients c ON c.id = s.client_id
            LEFT JOIN shifts sh ON sh.id = a.shift_id
            WHERE s.client_id = ?
            ORDER BY a.created_at DESC
            """,
            (client_id,),
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def _list_assignments(
    limit: int | None = None,
    offset: int = 0,
    employee_email: str | None = None,
    client_id: int | None = None,
    status: str | None = None,
) -> list[dict]:
    start = time.perf_counter()
    if limit is None and ADMIN_LIST_LIMIT > 0:
        limit = ADMIN_LIST_LIMIT
    conn = _db_connect()
    try:
        if not _table_exists(conn, "assignments"):
            return []
        base_query = """
            SELECT
                a.id,
                a.employee_user_id,
                u.name AS employee_name,
                u.email AS employee_email,
                a.site_id,
                s.name AS site_name,
                COALESCE(c.name, s.client_name) AS client_name,
                a.shift_id,
                sh.name AS shift_name,
                a.job_title,
                a.start_date,
                a.end_date,
                a.status,
                a.created_at,
                a.updated_at
            FROM assignments a
            JOIN users u ON u.id = a.employee_user_id
            JOIN sites s ON s.id = a.site_id
            LEFT JOIN clients c ON c.id = s.client_id
            LEFT JOIN shifts sh ON sh.id = a.shift_id
        """
        clauses = []
        params: list = []
        if employee_email:
            clauses.append("lower(u.email) LIKE ?")
            params.append(f"%{employee_email.strip().lower()}%")
        if client_id:
            clauses.append("s.client_id = ?")
            params.append(client_id)
        if status:
            clauses.append("a.status = ?")
            params.append(status)
        if clauses:
            base_query += " WHERE " + " AND ".join(clauses)
        base_query += " ORDER BY a.created_at DESC"
        if limit:
            base_query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        cur = conn.execute(base_query, tuple(params))
        rows = [dict(row) for row in cur.fetchall()]
        _perf_log("list_assignments", start, f"rows={len(rows)}")
        return rows
    finally:
        conn.close()


def _list_policies_by_client(client_id: int) -> list[dict]:
    conn = _db_connect()
    try:
        if not _table_exists(conn, "attendance_policies"):
            return []
        cur = conn.execute(
            """
            SELECT
                p.*,
                c.name AS direct_client_name,
                s.name AS site_name,
                COALESCE(c.name, cs.name, s.client_name) AS client_name,
                sh.name AS shift_name
            FROM attendance_policies p
            LEFT JOIN clients c ON c.id = p.client_id
            LEFT JOIN sites s ON s.id = p.site_id
            LEFT JOIN clients cs ON cs.id = s.client_id
            LEFT JOIN shifts sh ON sh.id = p.shift_id
            WHERE p.client_id = ? OR s.client_id = ?
            ORDER BY p.created_at DESC
            """,
            (client_id, client_id),
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def _list_policies() -> list[dict]:
    conn = _db_connect()
    try:
        if not _table_exists(conn, "attendance_policies"):
            return []
        cur = conn.execute(
            """
            SELECT
                p.*,
                c.name AS direct_client_name,
                s.name AS site_name,
                COALESCE(c.name, cs.name, s.client_name) AS client_name,
                sh.name AS shift_name
            FROM attendance_policies p
            LEFT JOIN clients c ON c.id = p.client_id
            LEFT JOIN sites s ON s.id = p.site_id
            LEFT JOIN clients cs ON cs.id = s.client_id
            LEFT JOIN shifts sh ON sh.id = p.shift_id
            ORDER BY p.created_at DESC
            """
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def _create_policy(
    scope_type: str,
    client_id: int | None,
    site_id: int | None,
    shift_id: int | None,
    effective_from: str,
    effective_to: str | None,
    work_duration_minutes: int | None,
    grace_minutes: int | None,
    late_threshold_minutes: int | None,
    allow_gps: int,
    require_selfie: int,
    allow_qr: int,
    auto_checkout: int,
    cutoff_time: str | None,
) -> int:
    scope = scope_type.upper()
    if scope == "CLIENT":
        site_id = None
    elif scope == "SITE":
        client_id = None
    conn = _db_connect()
    try:
        cur = conn.execute(
            """
            INSERT INTO attendance_policies (
                scope_type, client_id, site_id, shift_id, effective_from, effective_to,
                work_duration_minutes, grace_minutes, late_threshold_minutes,
                allow_gps, require_selfie, allow_qr, auto_checkout, cutoff_time,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                scope,
                client_id,
                site_id,
                shift_id,
                effective_from,
                effective_to or None,
                work_duration_minutes,
                grace_minutes,
                late_threshold_minutes,
                allow_gps,
                require_selfie,
                allow_qr,
                auto_checkout,
                cutoff_time or None,
                _now_ts(),
                _now_ts(),
            ),
        )
        policy_id = int(cur.lastrowid)
        return policy_id
    finally:
        conn.commit()
        conn.close()


def _update_policy(
    policy_id: int,
    scope_type: str,
    client_id: int | None,
    site_id: int | None,
    shift_id: int | None,
    effective_from: str,
    effective_to: str | None,
    work_duration_minutes: int | None,
    grace_minutes: int | None,
    late_threshold_minutes: int | None,
    allow_gps: int,
    require_selfie: int,
    allow_qr: int,
    auto_checkout: int,
    cutoff_time: str | None,
) -> None:
    scope = scope_type.upper()
    if scope == "CLIENT":
        site_id = None
    elif scope == "SITE":
        client_id = None
    conn = _db_connect()
    try:
        conn.execute(
            """
            UPDATE attendance_policies
            SET scope_type = ?, client_id = ?, site_id = ?, shift_id = ?, effective_from = ?, effective_to = ?,
                work_duration_minutes = ?, grace_minutes = ?, late_threshold_minutes = ?,
                allow_gps = ?, require_selfie = ?, allow_qr = ?, auto_checkout = ?, cutoff_time = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                scope,
                client_id,
                site_id,
                shift_id,
                effective_from,
                effective_to or None,
                work_duration_minutes,
                grace_minutes,
                late_threshold_minutes,
                allow_gps,
                require_selfie,
                allow_qr,
                auto_checkout,
                cutoff_time or None,
                _now_ts(),
                policy_id,
            ),
        )
    finally:
        conn.commit()
        conn.close()



def _create_assignment(
    employee_user_id: int,
    site_id: int,
    shift_id: int | None,
    job_title: str | None,
    start_date: str,
    end_date: str | None,
    status: str,
) -> int:
    if status == "ENDED" and not end_date:
        end_date = start_date
    conn = _db_connect()
    try:
        conn.execute("BEGIN IMMEDIATE")
        if status == "ACTIVE":
            conn.execute(
                """
                UPDATE assignments
                SET status = 'ENDED', end_date = ?, updated_at = ?
                WHERE employee_user_id = ? AND status = 'ACTIVE'
                """,
                (start_date, _now_ts(), employee_user_id),
            )
        cur = conn.execute(
            """
            INSERT INTO assignments (
                employee_user_id, site_id, shift_id, job_title, start_date, end_date,
                status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                employee_user_id,
                site_id,
                shift_id,
                job_title,
                start_date,
                end_date,
                status,
                _now_ts(),
                _now_ts(),
            ),
        )
        assignment_id = int(cur.lastrowid)
        return assignment_id
    finally:
        conn.commit()
        conn.close()


def _create_assignment_with_log(
    *,
    actor: User | None,
    employee_user_id: int,
    site_id: int,
    shift_id: int | None,
    job_title: str | None,
    start_date: str,
    end_date: str | None,
    status: str,
    summary: str,
    portal: str,
    extra_details: dict | None = None,
) -> int:
    assignment_id = _create_assignment(
        employee_user_id=employee_user_id,
        site_id=site_id,
        shift_id=shift_id,
        job_title=job_title,
        start_date=start_date,
        end_date=end_date,
        status=status,
    )
    details: dict = {
        "employee_user_id": employee_user_id,
        "site_id": site_id,
        "shift_id": shift_id,
        "job_title": job_title,
        "start_date": start_date,
        "end_date": end_date,
        "status": status,
        "portal": portal,
    }
    if extra_details:
        details.update(extra_details)
    _log_audit_event(
        entity_type="assignment",
        entity_id=assignment_id,
        action="CREATE",
        actor=actor,
        summary=summary,
        details=details,
    )
    return assignment_id


def _update_assignment(
    assignment_id: int,
    employee_user_id: int,
    site_id: int,
    shift_id: int | None,
    job_title: str | None,
    start_date: str,
    end_date: str | None,
    status: str,
) -> None:
    if status == "ENDED" and not end_date:
        end_date = start_date
    conn = _db_connect()
    try:
        conn.execute("BEGIN IMMEDIATE")
        if status == "ACTIVE":
            conn.execute(
                """
                UPDATE assignments
                SET status = 'ENDED', end_date = ?, updated_at = ?
                WHERE employee_user_id = ? AND status = 'ACTIVE' AND id != ?
                """,
                (start_date, _now_ts(), employee_user_id, assignment_id),
            )
        conn.execute(
            """
            UPDATE assignments
            SET employee_user_id = ?, site_id = ?, shift_id = ?, job_title = ?, start_date = ?, end_date = ?,
                status = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                employee_user_id,
                site_id,
                shift_id,
                job_title,
                start_date,
                end_date,
                status,
                _now_ts(),
                assignment_id,
            ),
        )
    finally:
        conn.commit()
        conn.close()


def _end_assignment(assignment_id: int) -> None:
    conn = _db_connect()
    try:
        conn.execute(
            """
            UPDATE assignments
            SET status = 'ENDED',
                end_date = CASE
                    WHEN end_date IS NULL OR end_date = '' THEN ?
                    ELSE end_date
                END,
                updated_at = ?
            WHERE id = ?
            """,
            (_today_key(), _now_ts(), assignment_id),
        )
    finally:
        conn.commit()
        conn.close()


def _end_assignment_with_date(assignment_id: int, end_date: str) -> None:
    conn = _db_connect()
    try:
        conn.execute(
            """
            UPDATE assignments
            SET status = 'ENDED',
                end_date = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (end_date, _now_ts(), assignment_id),
        )
    finally:
        conn.commit()
        conn.close()


def _delete_assignment(assignment_id: int) -> None:
    conn = _db_connect()
    try:
        conn.execute("DELETE FROM assignments WHERE id = ?", (assignment_id,))
    finally:
        conn.commit()
        conn.close()


def _create_site(
    client_id: int,
    name: str,
    latitude: float,
    longitude: float,
    radius_meters: int,
    notes: str | None,
    timezone: str | None,
    work_mode: str | None,
    pic_name: str | None = None,
    pic_email: str | None = None,
) -> int:
    client_name = _client_name_by_id(client_id) or ""
    conn = _db_connect()
    try:
        cur = conn.execute(
            """
            INSERT INTO sites (
                client_id, client_name, name, timezone, work_mode, latitude,
                longitude, radius_meters, notes, pic_name, pic_email, is_active, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                client_id,
                client_name,
                name,
                timezone or "Asia/Jakarta",
                work_mode or None,
                latitude,
                longitude,
                radius_meters,
                notes or None,
                pic_name,
                pic_email,
                1,
                _now_ts(),
            ),
        )
        return int(cur.lastrowid)
    finally:
        conn.commit()
        conn.close()


def _update_site(
    site_id: int,
    client_id: int,
    name: str,
    latitude: float,
    longitude: float,
    radius_meters: int,
    notes: str | None,
    timezone: str | None,
    work_mode: str | None,
    pic_name: str | None = None,
    pic_email: str | None = None,
) -> None:
    client_name = _client_name_by_id(client_id) or ""
    conn = _db_connect()
    try:
        conn.execute(
            """
            UPDATE sites
            SET client_id = ?, client_name = ?, name = ?, timezone = ?, work_mode = ?,
                latitude = ?, longitude = ?, radius_meters = ?, notes = ?, pic_name = ?, pic_email = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                client_id,
                client_name,
                name,
                timezone or None,
                work_mode or None,
                latitude,
                longitude,
                radius_meters,
                notes or None,
                pic_name,
                pic_email,
                _now_ts(),
                site_id,
            ),
        )
    finally:
        conn.commit()
        conn.close()


def _end_policy(policy_id: int) -> None:
    conn = _db_connect()
    try:
        conn.execute(
            """
            UPDATE attendance_policies
            SET effective_to = ?, updated_at = ?
            WHERE id = ?
            """,
            (_today_key(), _now_ts(), policy_id),
        )
    finally:
        conn.commit()
        conn.close()


def _toggle_site(site_id: int, is_active: int) -> None:
    conn = _db_connect()
    try:
        conn.execute(
            "UPDATE sites SET is_active = ? WHERE id = ?",
            (is_active, site_id),
        )
    finally:
        conn.commit()
        conn.close()


def _delete_policy(policy_id: int) -> None:
    conn = _db_connect()
    try:
        conn.execute("DELETE FROM attendance_policies WHERE id = ?", (policy_id,))
    finally:
        conn.commit()
        conn.close()


def _list_shifts() -> list[dict]:
    conn = _db_connect()
    try:
        cur = conn.execute(
            """
            SELECT id, name, start_time, end_time, grace_minutes, is_active, created_at
            FROM shifts
            ORDER BY created_at DESC
            """
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def _create_shift(name: str, start_time: str | None, end_time: str | None, grace_minutes: int) -> None:
    conn = _db_connect()
    try:
        conn.execute(
            """
            INSERT INTO shifts (name, start_time, end_time, grace_minutes, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, start_time or None, end_time or None, grace_minutes, 1, _now_ts()),
        )
    finally:
        conn.commit()
        conn.close()


def _update_shift(shift_id: int, name: str, start_time: str | None, end_time: str | None, grace_minutes: int) -> None:
    conn = _db_connect()
    try:
        conn.execute(
            """
            UPDATE shifts
            SET name = ?, start_time = ?, end_time = ?, grace_minutes = ?
            WHERE id = ?
            """,
            (name, start_time or None, end_time or None, grace_minutes, shift_id),
        )
    finally:
        conn.commit()
        conn.close()


def _toggle_shift(shift_id: int, is_active: int) -> None:
    conn = _db_connect()
    try:
        conn.execute(
            "UPDATE shifts SET is_active = ? WHERE id = ?",
            (is_active, shift_id),
        )
    finally:
        conn.commit()
        conn.close()


def _delete_shift(shift_id: int) -> None:
    conn = _db_connect()
    try:
        conn.execute("DELETE FROM shifts WHERE id = ?", (shift_id,))
    finally:
        conn.commit()
        conn.close()


def _get_supervisor_sites_map() -> dict[int, set[int]]:
    conn = _db_connect()
    try:
        cur = conn.execute("SELECT supervisor_user_id, site_id FROM supervisor_sites")
        mapping: dict[int, set[int]] = {}
        for row in cur.fetchall():
            mapping.setdefault(int(row["supervisor_user_id"]), set()).add(int(row["site_id"]))
        return mapping
    finally:
        conn.close()


def _set_supervisor_sites(supervisor_user_id: int, site_ids: list[int]) -> None:
    conn = _db_connect()
    try:
        conn.execute("DELETE FROM supervisor_sites WHERE supervisor_user_id = ?", (supervisor_user_id,))
        for site_id in site_ids:
            conn.execute(
                "INSERT OR IGNORE INTO supervisor_sites (supervisor_user_id, site_id) VALUES (?, ?)",
                (supervisor_user_id, site_id),
            )
    finally:
        conn.commit()
        conn.close()


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    )
    return cur.fetchone() is not None


def _table_columns(conn: sqlite3.Connection, name: str) -> set[str]:
    cur = conn.execute(f"PRAGMA table_info({name})")
    return {row[1] for row in cur.fetchall()}


def _foreign_key_exists(
    conn: sqlite3.Connection,
    table: str,
    column: str,
    ref_table: str,
    ref_column: str,
) -> bool:
    try:
        cur = conn.execute(f"PRAGMA foreign_key_list({table})")
    except sqlite3.OperationalError:
        return False
    for row in cur.fetchall():
        if (
            row["from"] == column
            and row["table"] == ref_table
            and row["to"] == ref_column
        ):
            return True
    return False


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = _table_columns(conn, table)
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {definition}")


def _cleanup_orphans(conn: sqlite3.Connection) -> None:
    if _table_exists(conn, "supervisor_sites"):
        conn.execute(
            """
            DELETE FROM supervisor_sites
            WHERE supervisor_user_id NOT IN (SELECT id FROM users)
               OR site_id NOT IN (SELECT id FROM sites)
            """
        )
    if _table_exists(conn, "employee_site"):
        conn.execute(
            """
            DELETE FROM employee_site
            WHERE employee_user_id NOT IN (SELECT id FROM users)
               OR site_id NOT IN (SELECT id FROM sites)
            """
        )
    if _table_exists(conn, "assignments"):
        conn.execute(
            """
            DELETE FROM assignments
            WHERE employee_user_id NOT IN (SELECT id FROM users)
               OR site_id NOT IN (SELECT id FROM sites)
               OR (shift_id IS NOT NULL AND shift_id NOT IN (SELECT id FROM shifts))
            """
        )
    if _table_exists(conn, "attendance_policies"):
        conn.execute(
            """
            DELETE FROM attendance_policies
            WHERE (client_id IS NOT NULL AND client_id NOT IN (SELECT id FROM clients))
               OR (site_id IS NOT NULL AND site_id NOT IN (SELECT id FROM sites))
               OR (shift_id IS NOT NULL AND shift_id NOT IN (SELECT id FROM shifts))
            """
        )
    if _table_exists(conn, "client_contacts"):
        conn.execute(
            """
            DELETE FROM client_contacts
            WHERE client_id NOT IN (SELECT id FROM clients)
            """
        )
    if _table_exists(conn, "manual_attendance_requests"):
        conn.execute(
            """
            DELETE FROM manual_attendance_requests
            WHERE created_by_user_id NOT IN (SELECT id FROM users)
            """
        )
        conn.execute(
            """
            UPDATE manual_attendance_requests
            SET employee_id = NULL
            WHERE employee_id IS NOT NULL
              AND employee_id NOT IN (SELECT id FROM employees)
            """
        )
    if _table_exists(conn, "attendance"):
        conn.execute(
            """
            UPDATE attendance
            SET employee_id = NULL
            WHERE employee_id IS NOT NULL
              AND employee_id NOT IN (SELECT id FROM employees)
            """
        )
        conn.execute(
            """
            UPDATE attendance
            SET manual_request_id = NULL
            WHERE manual_request_id IS NOT NULL
              AND manual_request_id NOT IN (SELECT id FROM manual_attendance_requests)
            """
        )


def _dedupe_employees(conn: sqlite3.Connection) -> None:
    if not _table_exists(conn, "employees"):
        return
    rows = conn.execute(
        "SELECT id, email, nik, no_hp, is_active FROM employees"
    ).fetchall()
    by_email: dict[str, list[sqlite3.Row]] = {}
    by_nik: dict[str, list[sqlite3.Row]] = {}
    by_phone: dict[str, list[sqlite3.Row]] = {}
    for row in rows:
        email = (row["email"] or "").strip().lower()
        nik = (row["nik"] or "").strip()
        phone = _normalize_phone(row["no_hp"] or "")
        if email:
            by_email.setdefault(email, []).append(row)
        if nik:
            by_nik.setdefault(nik, []).append(row)
        if phone:
            by_phone.setdefault(phone, []).append(row)

    def _dedupe_email(value: str, employee_id: int) -> str:
        if "@" in value:
            local, domain = value.split("@", 1)
            return f"{local}+dup{employee_id}@{domain}"
        return f"{value}.dup{employee_id}"

    def _dedupe_value(value: str, employee_id: int) -> str:
        return f"{value}-dup-{employee_id}"

    def _apply_updates(employee_id: int, updates: dict[str, str]) -> None:
        if not updates:
            return
        assignments = ", ".join(f"{key} = ?" for key in updates.keys())
        values = list(updates.values()) + [employee_id]
        conn.execute(
            f"UPDATE employees SET {assignments}, is_active = 0 WHERE id = ?",
            values,
        )

    for duplicates in by_email.values():
        if len(duplicates) <= 1:
            continue
        duplicates.sort(key=lambda row: int(row["id"]))
        for row in duplicates[1:]:
            value = (row["email"] or "").strip().lower()
            _apply_updates(row["id"], {"email": _dedupe_email(value, row["id"])})

    for duplicates in by_nik.values():
        if len(duplicates) <= 1:
            continue
        duplicates.sort(key=lambda row: int(row["id"]))
        for row in duplicates[1:]:
            value = (row["nik"] or "").strip()
            _apply_updates(row["id"], {"nik": _dedupe_value(value, row["id"])})

    for duplicates in by_phone.values():
        if len(duplicates) <= 1:
            continue
        duplicates.sort(key=lambda row: int(row["id"]))
        for row in duplicates[1:]:
            value = (row["no_hp"] or "").strip()
            _apply_updates(row["id"], {"no_hp": _dedupe_value(value, row["id"])})


def _init_db() -> None:
    conn = _db_connect()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                role TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TEXT,
                updated_at TEXT,
                must_change_password INTEGER DEFAULT 0,
                selfie_path TEXT,
                client_id INTEGER,
                site_id INTEGER
            )
            """
        )
        if _table_exists(conn, "users"):
            conn.execute(
                "UPDATE users SET role = 'hr_superadmin' WHERE role = 'superadmin'"
            )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                legal_name TEXT,
                tax_id TEXT,
                status TEXT NOT NULL DEFAULT 'ACTIVE',
                contract_no TEXT,
                contract_start TEXT,
                contract_end TEXT,
                address TEXT NOT NULL,
                office_email TEXT NOT NULL,
                office_phone TEXT NOT NULL,
                pic_name TEXT NOT NULL,
                pic_title TEXT NOT NULL,
                pic_phone TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                notes TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS client_contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                contact_type TEXT NOT NULL,
                name TEXT NOT NULL,
                title TEXT,
                phone TEXT,
                email TEXT,
                is_primary INTEGER DEFAULT 0,
                notes TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nik TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                no_hp TEXT NOT NULL,
                address TEXT NOT NULL,
                gender TEXT NOT NULL,
                status_nikah TEXT NOT NULL,
                notes TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT,
                site_id INTEGER
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS employee_registration_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year_month TEXT NOT NULL,
                seq INTEGER NOT NULL,
                registrant_count INTEGER NOT NULL,
                used_count INTEGER DEFAULT 0,
                code TEXT NOT NULL,
                created_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                client_name TEXT,
                name TEXT NOT NULL,
                address TEXT,
                timezone TEXT,
                work_mode TEXT,
                latitude REAL,
                longitude REAL,
                radius_meters INTEGER,
                notes TEXT,
                pic_name TEXT,
                pic_email TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (client_id) REFERENCES clients(id) ON UPDATE CASCADE ON DELETE RESTRICT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS shifts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                start_time TEXT,
                end_time TEXT,
                grace_minutes INTEGER DEFAULT 0,
                rules_json TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS supervisor_sites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supervisor_user_id INTEGER,
                site_id INTEGER,
                UNIQUE(supervisor_user_id, site_id),
                FOREIGN KEY (supervisor_user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS employee_site (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_user_id INTEGER,
                site_id INTEGER,
                UNIQUE(employee_user_id, site_id),
                FOREIGN KEY (employee_user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_user_id INTEGER NOT NULL,
                site_id INTEGER NOT NULL,
                shift_id INTEGER,
                job_title TEXT,
                start_date TEXT NOT NULL,
                end_date TEXT,
                status TEXT NOT NULL DEFAULT 'ACTIVE',
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (employee_user_id) REFERENCES users(id) ON DELETE RESTRICT,
                FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE RESTRICT,
                FOREIGN KEY (shift_id) REFERENCES shifts(id) ON DELETE RESTRICT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance_policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scope_type TEXT NOT NULL,
                client_id INTEGER,
                site_id INTEGER,
                shift_id INTEGER,
                effective_from TEXT NOT NULL,
                effective_to TEXT,
                work_duration_minutes INTEGER,
                grace_minutes INTEGER,
                late_threshold_minutes INTEGER,
                allow_gps INTEGER DEFAULT 1,
                require_selfie INTEGER DEFAULT 0,
                allow_qr INTEGER DEFAULT 1,
                auto_checkout INTEGER DEFAULT 0,
                cutoff_time TEXT,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE RESTRICT,
                FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE RESTRICT,
                FOREIGN KEY (shift_id) REFERENCES shifts(id) ON DELETE RESTRICT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS leave_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_email TEXT NOT NULL,
                leave_type TEXT NOT NULL,
                date_from TEXT NOT NULL,
                date_to TEXT NOT NULL,
                reason TEXT NOT NULL,
                attachment TEXT,
                attachment_path TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                approver_email TEXT,
                approved_at TEXT,
                note TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                used_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user ON password_reset_tokens(user_id)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id INTEGER,
                action TEXT NOT NULL,
                actor_email TEXT NOT NULL,
                actor_role TEXT NOT NULL,
                summary TEXT NOT NULL,
                details_json TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity_type, entity_id)"
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS manual_attendance_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER,
                employee_name TEXT,
                employee_email TEXT,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                action TEXT NOT NULL,
                reason TEXT NOT NULL,
                created_by_user_id INTEGER NOT NULL,
                created_by_email TEXT NOT NULL,
                created_by_role TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING',
                reviewed_by_user_id TEXT,
                reviewed_at TEXT,
                review_note TEXT,
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE SET NULL,
                FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE RESTRICT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS role_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL UNIQUE,
                permissions_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        if _table_exists(conn, "role_permissions"):
            conn.execute(
                "UPDATE role_permissions SET role = 'hr_superadmin' WHERE role = 'superadmin'"
            )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_manual_attendance_status ON manual_attendance_requests(status)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_manual_attendance_created_at ON manual_attendance_requests(created_at)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_manual_attendance_created_by ON manual_attendance_requests(created_by_user_id)"
        )

        if not _table_exists(conn, "attendance"):
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER,
                    employee_name TEXT,
                    employee_email TEXT,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    action TEXT NOT NULL,
                    method TEXT,
                    selfie_path TEXT,
                    source TEXT,
                    manual_request_id INTEGER,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE SET NULL,
                    FOREIGN KEY (manual_request_id) REFERENCES manual_attendance_requests(id) ON DELETE SET NULL
                )
                """
            )
        else:
            _ensure_column(conn, "users", "client_id", "client_id INTEGER")
            _ensure_column(conn, "users", "site_id", "site_id INTEGER")
            _ensure_column(conn, "attendance", "source", "source TEXT")
            _ensure_column(conn, "attendance", "manual_request_id", "manual_request_id INTEGER")
            _ensure_column(conn, "attendance", "selfie_path", "selfie_path TEXT")
            _ensure_column(conn, "sites", "client_name", "client_name TEXT")
            _ensure_column(conn, "sites", "client_id", "client_id INTEGER")
            _ensure_column(conn, "sites", "address", "address TEXT")
            _ensure_column(conn, "sites", "timezone", "timezone TEXT")
            _ensure_column(conn, "sites", "work_mode", "work_mode TEXT")
            _ensure_column(conn, "sites", "latitude", "latitude REAL")
            _ensure_column(conn, "sites", "longitude", "longitude REAL")
            _ensure_column(conn, "sites", "radius_meters", "radius_meters INTEGER")
            _ensure_column(conn, "sites", "pic_name", "pic_name TEXT")
            _ensure_column(conn, "sites", "pic_email", "pic_email TEXT")
            _ensure_column(conn, "sites", "updated_at", "updated_at TEXT")
        if _table_exists(conn, "clients"):
            _ensure_column(conn, "clients", "is_active", "is_active INTEGER DEFAULT 1")
            _ensure_column(conn, "clients", "legal_name", "legal_name TEXT")
            _ensure_column(conn, "clients", "tax_id", "tax_id TEXT")
            _ensure_column(conn, "clients", "status", "status TEXT NOT NULL DEFAULT 'ACTIVE'")
            _ensure_column(conn, "clients", "contract_no", "contract_no TEXT")
            _ensure_column(conn, "clients", "contract_start", "contract_start TEXT")
            _ensure_column(conn, "clients", "contract_end", "contract_end TEXT")
            _ensure_column(conn, "clients", "updated_at", "updated_at TEXT")
            try:
                conn.execute(
                    "CREATE UNIQUE INDEX IF NOT EXISTS idx_clients_unique_name ON clients(lower(name))"
                )
                conn.execute(
                    "CREATE UNIQUE INDEX IF NOT EXISTS idx_clients_unique_legal_name ON clients(lower(legal_name))"
                )
            except sqlite3.IntegrityError:
                pass
        if _table_exists(conn, "employees"):
            _ensure_column(conn, "employees", "nik", "nik TEXT")
            _ensure_column(conn, "employees", "name", "name TEXT")
            _ensure_column(conn, "employees", "email", "email TEXT")
            _ensure_column(conn, "employees", "no_hp", "no_hp TEXT")
            _ensure_column(conn, "employees", "address", "address TEXT")
            _ensure_column(conn, "employees", "gender", "gender TEXT")
            _ensure_column(conn, "employees", "status_nikah", "status_nikah TEXT")
            _ensure_column(conn, "employees", "notes", "notes TEXT")
            _ensure_column(conn, "employees", "is_active", "is_active INTEGER DEFAULT 1")
            _ensure_column(conn, "employees", "created_at", "created_at TEXT")
            _ensure_column(conn, "employees", "site_id", "site_id INTEGER")
            _dedupe_employees(conn)
            try:
                conn.execute(
                    """
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_employees_unique_email
                    ON employees(lower(email))
                    WHERE email IS NOT NULL AND trim(email) != ''
                    """
                )
                conn.execute(
                    """
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_employees_unique_nik
                    ON employees(nik)
                    WHERE nik IS NOT NULL AND trim(nik) != ''
                    """
                )
                conn.execute(
                    """
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_employees_unique_phone
                    ON employees(no_hp)
                    WHERE no_hp IS NOT NULL AND trim(no_hp) != ''
                    """
                )
            except sqlite3.IntegrityError:
                pass
        if _table_exists(conn, "assignments"):
            _ensure_column(conn, "assignments", "shift_id", "shift_id INTEGER")
        if _table_exists(conn, "attendance_policies"):
            _ensure_column(conn, "attendance_policies", "shift_id", "shift_id INTEGER")
        if _table_exists(conn, "manual_attendance_requests"):
            _ensure_column(conn, "manual_attendance_requests", "created_by_email", "created_by_email TEXT")
            conn.execute(
                """
                UPDATE manual_attendance_requests
                SET created_by_email = created_by_user_id
                WHERE (created_by_email IS NULL OR created_by_email = '')
                  AND created_by_user_id LIKE '%@%'
                """
            )
        _cleanup_orphans(conn)
        if _table_exists(conn, "attendance"):
            try:
                conn.execute(
                    """
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_attendance_unique_daily
                    ON attendance(employee_email, date, action)
                    """
                )
            except sqlite3.IntegrityError:
                pass
        if _table_exists(conn, "employee_registration_codes"):
            _ensure_column(conn, "employee_registration_codes", "year_month", "year_month TEXT")
            _ensure_column(conn, "employee_registration_codes", "seq", "seq INTEGER")
            _ensure_column(conn, "employee_registration_codes", "registrant_count", "registrant_count INTEGER")
            _ensure_column(conn, "employee_registration_codes", "used_count", "used_count INTEGER DEFAULT 0")
            _ensure_column(conn, "employee_registration_codes", "code", "code TEXT")
            _ensure_column(conn, "employee_registration_codes", "created_at", "created_at TEXT")
        if _table_exists(conn, "leave_requests"):
            _ensure_column(conn, "leave_requests", "employee_email", "employee_email TEXT")
            _ensure_column(conn, "leave_requests", "leave_type", "leave_type TEXT")
            _ensure_column(conn, "leave_requests", "date_from", "date_from TEXT")
            _ensure_column(conn, "leave_requests", "date_to", "date_to TEXT")
            _ensure_column(conn, "leave_requests", "reason", "reason TEXT")
            _ensure_column(conn, "leave_requests", "attachment", "attachment TEXT")
            _ensure_column(conn, "leave_requests", "attachment_path", "attachment_path TEXT")
            _ensure_column(conn, "leave_requests", "status", "status TEXT NOT NULL DEFAULT 'pending'")
            _ensure_column(conn, "leave_requests", "approver_email", "approver_email TEXT")
            _ensure_column(conn, "leave_requests", "approved_at", "approved_at TEXT")
            _ensure_column(conn, "leave_requests", "note", "note TEXT")
            _ensure_column(conn, "leave_requests", "created_at", "created_at TEXT")
            _ensure_column(conn, "leave_requests", "updated_at", "updated_at TEXT")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_leave_requests_status ON leave_requests(status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_leave_requests_employee ON leave_requests(employee_email)"
            )
        if _table_exists(conn, "client_contacts"):
            _ensure_column(conn, "client_contacts", "client_id", "client_id INTEGER")
            _ensure_column(conn, "client_contacts", "contact_type", "contact_type TEXT")
            _ensure_column(conn, "client_contacts", "name", "name TEXT")
            _ensure_column(conn, "client_contacts", "title", "title TEXT")
            _ensure_column(conn, "client_contacts", "phone", "phone TEXT")
            _ensure_column(conn, "client_contacts", "email", "email TEXT")
            _ensure_column(conn, "client_contacts", "is_primary", "is_primary INTEGER DEFAULT 0")
            _ensure_column(conn, "client_contacts", "notes", "notes TEXT")
            _ensure_column(conn, "client_contacts", "created_at", "created_at TEXT")
            _ensure_column(conn, "client_contacts", "updated_at", "updated_at TEXT")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_client_contacts_client ON client_contacts(client_id)"
            )
            try:
                conn.execute(
                    """
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_client_contacts_primary
                    ON client_contacts(client_id, contact_type)
                    WHERE is_primary = 1
                    """
                )
            except sqlite3.OperationalError:
                pass

        if _table_exists(conn, "sites") and _table_exists(conn, "clients"):
            cur = conn.execute(
                """
                SELECT id, client_name
                FROM sites
                WHERE client_id IS NULL
                  AND client_name IS NOT NULL
                  AND client_name != ''
                """
            )
            for row in cur.fetchall():
                client_row = conn.execute(
                    "SELECT id FROM clients WHERE lower(name) = ?",
                    (row["client_name"].lower(),),
                ).fetchone()
                if client_row:
                    conn.execute(
                        "UPDATE sites SET client_id = ? WHERE id = ?",
                        (client_row["id"], row["id"]),
                    )
            conn.execute(
                """
                UPDATE sites
                SET client_id = NULL
                WHERE client_id IS NOT NULL
                  AND client_id NOT IN (SELECT id FROM clients)
                """
            )
            if not _foreign_key_exists(conn, "sites", "client_id", "clients", "id"):
                conn.execute("ALTER TABLE sites RENAME TO sites_old")
                conn.execute(
                    """
                    CREATE TABLE sites (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        client_id INTEGER,
                        client_name TEXT,
                        name TEXT NOT NULL,
                        address TEXT,
                        timezone TEXT,
                        work_mode TEXT,
                        latitude REAL,
                        longitude REAL,
                        radius_meters INTEGER,
                        notes TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY (client_id) REFERENCES clients(id)
                            ON UPDATE CASCADE
                            ON DELETE RESTRICT
                    )
                    """
                )
                conn.execute(
                    """
                    INSERT INTO sites (
                        id, client_id, client_name, name, address, timezone, work_mode,
                        latitude, longitude, radius_meters, notes, is_active, created_at, updated_at
                    )
                    SELECT
                        id, client_id, client_name, name, address, timezone, work_mode,
                        latitude, longitude, radius_meters, notes, is_active, created_at, updated_at
                    FROM sites_old
                    """
                )
                conn.execute("DROP TABLE sites_old")

        if _table_exists(conn, "assignments"):
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_assignments_user_status ON assignments(employee_user_id, status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_assignments_site_status ON assignments(site_id, status)"
            )
            if _table_exists(conn, "employee_site"):
                cur = conn.execute("SELECT COUNT(1) AS total FROM assignments")
                row = cur.fetchone()
                total = row["total"] if row else 0
                if total == 0:
                    cur = conn.execute("SELECT employee_user_id, site_id FROM employee_site")
                    for row in cur.fetchall():
                        conn.execute(
                            """
                            INSERT INTO assignments (
                                employee_user_id, site_id, job_title, start_date, end_date,
                                status, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                row["employee_user_id"],
                                row["site_id"],
                                None,
                                _today_key(),
                                None,
                                "ACTIVE",
                                _now_ts(),
                                _now_ts(),
                            ),
                        )

        if ENABLE_SEED_DATA:
            _seed_users(conn)
            _seed_employees(conn)
    finally:
        conn.commit()
        conn.close()


def _seed_users(conn: sqlite3.Connection) -> None:
    for seed in SEED_USERS:
        email = seed["email"].lower()
        cur = conn.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cur.fetchone():
            continue
        conn.execute(
            """
            INSERT INTO users (
                name, email, role, password_hash, is_active,
                created_at, updated_at, must_change_password, client_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                seed.get("name") or "",
                email,
                seed["role"],
                generate_password_hash(seed["password"]),
                1,
                _now_ts(),
                _now_ts(),
                0,
                seed.get("client_id"),
            ),
        )


def _seed_employees(conn: sqlite3.Connection) -> None:
    if not _table_exists(conn, "employees"):
        return
    for seed in SEED_EMPLOYEES:
        email = (seed.get("email") or "").lower()
        nik = seed.get("nik") or ""
        cur = conn.execute(
            "SELECT id FROM employees WHERE email = ? OR nik = ?",
            (email, nik),
        )
        if cur.fetchone():
            continue
        conn.execute(
            """
            INSERT INTO employees (
                nik, name, email, no_hp, address, gender,
                status_nikah, notes, is_active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                seed.get("nik") or "",
                seed.get("name") or "",
                email,
                seed.get("no_hp") or "",
                seed.get("address") or "",
                seed.get("gender") or "",
                seed.get("status_nikah") or "",
                seed.get("notes") or None,
                int(seed.get("is_active") or 0),
                _now_ts(),
            ),
        )


def _employee_by_id(employee_id: str | int | None) -> dict | None:
    try:
        target = int(employee_id)
    except (TypeError, ValueError):
        return None
    for employee in _employees():
        if int(employee.get("id", 0)) == target:
            return employee
    return None


def _has_supervisor_account() -> bool:
    conn = _db_connect()
    try:
        cur = conn.execute(
            "SELECT 1 FROM users WHERE role = 'supervisor' AND is_active = 1 LIMIT 1"
        )
        return cur.fetchone() is not None
    finally:
        conn.close()


def _has_manager_operational() -> bool:
    conn = _db_connect()
    try:
        cur = conn.execute(
            "SELECT 1 FROM users WHERE role = 'manager_operational' AND is_active = 1 LIMIT 1"
        )
        return cur.fetchone() is not None
    finally:
        conn.close()


def _can_submit_manual(user: User) -> bool:
    return user.role in ADMIN_ROLE_OPTIONS


def _can_approve_leave(user: User) -> bool:
    return user.role in APPROVER_ROLES


def _can_approve_manual(user: User) -> bool:
    return user.role in APPROVER_ROLES


def _get_supervisor_site_ids(user_id: int) -> set[int]:
    conn = _db_connect()
    try:
        if not _table_exists(conn, "supervisor_sites"):
            return set()
        cur = conn.execute(
            "SELECT site_id FROM supervisor_sites WHERE supervisor_user_id = ?",
            (user_id,),
        )
        return {int(row["site_id"]) for row in cur.fetchall()}
    finally:
        conn.close()


def _approver_scope_emails(user: User | None) -> set[str] | None:
    if not user:
        return set()
    if user.role == "hr_superadmin":
        return None
    client_scope = _approver_client_scope_id(user)
    if client_scope:
        today = _today_key()
        emails: set[str] = set()
        for row in _list_active_assignments(today):
            if int(_row_get(row, "client_id") or 0) == client_scope:
                email = (_row_get(row, "employee_email") or "").strip().lower()
                if email:
                    emails.add(email)
        return emails
    site_ids = _get_supervisor_site_ids(user.id)
    if not site_ids:
        return set()
    today = _today_key()
    emails: set[str] = set()
    for row in _list_active_assignments(today):
        if int(_row_get(row, "site_id") or 0) in site_ids:
            email = (_row_get(row, "employee_email") or "").strip().lower()
            if email:
                emails.add(email)
    return emails


def _approver_can_handle(user: User | None, employee_email: str) -> bool:
    scope = _approver_scope_emails(user)
    if scope is None:
        return True
    return employee_email.strip().lower() in scope


def _create_leave_request(
    employee_email: str,
    leave_type: str,
    date_from: str,
    date_to: str,
    reason: str,
    attachment: str | None,
    attachment_path: str | None,
) -> int:
    conn = _db_connect()
    try:
        cur = conn.execute(
            """
            INSERT INTO leave_requests (
                employee_email, leave_type, date_from, date_to, reason,
                attachment, attachment_path, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                employee_email,
                leave_type,
                date_from,
                date_to,
                reason,
                attachment,
                attachment_path,
                "pending",
                _now_ts(),
                _now_ts(),
            ),
        )
        return int(cur.lastrowid)
    finally:
        conn.commit()
        conn.close()


def _list_leave_requests_by_email(employee_email: str) -> list[dict]:
    conn = _db_connect()
    try:
        if not _table_exists(conn, "leave_requests"):
            return []
        cur = conn.execute(
            """
            SELECT
                id,
                employee_email,
                leave_type AS type,
                date_from,
                date_to,
                reason,
                attachment,
                attachment_path,
                status,
                approver_email AS approver,
                approved_at,
                note,
                created_at,
                updated_at
            FROM leave_requests
            WHERE employee_email = ?
            ORDER BY created_at DESC
            """,
            (employee_email,),
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def _list_leave_pending(user: User | None = None, limit: int | None = None) -> list[dict]:
    start = time.perf_counter()
    if limit is None and PENDING_LIST_LIMIT > 0:
        limit = PENDING_LIST_LIMIT
    conn = _db_connect()
    try:
        if not _table_exists(conn, "leave_requests"):
            return []
        scope = _approver_scope_emails(user)
        if scope is not None:
            if not scope:
                return []
            placeholders = ",".join("?" for _ in scope)
            params = [*sorted(scope)]
            query = f"""
                SELECT
                    id,
                    employee_email,
                    leave_type AS type,
                    date_from,
                    date_to,
                    reason,
                    attachment,
                    attachment_path,
                    status,
                    approver_email AS approver,
                    approved_at,
                    note,
                    created_at,
                    updated_at
                FROM leave_requests
                WHERE status = 'pending'
                  AND lower(employee_email) IN ({placeholders})
                ORDER BY created_at DESC
            """
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            cur = conn.execute(query, params)
        else:
            query = """
                SELECT
                    id,
                    employee_email,
                    leave_type AS type,
                    date_from,
                    date_to,
                    reason,
                    attachment,
                    attachment_path,
                    status,
                    approver_email AS approver,
                    approved_at,
                    note,
                    created_at,
                    updated_at
                FROM leave_requests
                WHERE status = 'pending'
                ORDER BY created_at DESC
            """
            params: tuple = ()
            if limit:
                query += " LIMIT ?"
                params = (limit,)
            cur = conn.execute(query, params)
        rows = [dict(row) for row in cur.fetchall()]
        _perf_log("list_leave_pending", start, f"rows={len(rows)}")
        return rows
    finally:
        conn.close()


def _get_leave_request_by_id(request_id: int) -> dict | None:
    conn = _db_connect()
    try:
        if not _table_exists(conn, "leave_requests"):
            return None
        cur = conn.execute(
            """
            SELECT
                id,
                employee_email,
                leave_type AS type,
                date_from,
                date_to,
                reason,
                attachment,
                attachment_path,
                status,
                approver_email AS approver,
                approved_at,
                note,
                created_at,
                updated_at
            FROM leave_requests
            WHERE id = ?
            """,
            (request_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def _update_leave_request_status(
    request_id: int,
    status: str,
    approver_email: str,
    note: str | None,
) -> None:
    conn = _db_connect()
    try:
        conn.execute(
            """
            UPDATE leave_requests
            SET status = ?, approver_email = ?, approved_at = ?, note = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, approver_email, _now_ts(), note, _now_ts(), request_id),
        )
    finally:
        conn.commit()
        conn.close()


def _list_leave_active_for_date(today: str) -> list[dict]:
    start = time.perf_counter()
    conn = _db_connect()
    try:
        if not _table_exists(conn, "leave_requests"):
            return []
        cur = conn.execute(
            """
            SELECT employee_email, status, date_from, date_to
            FROM leave_requests
            WHERE status != 'rejected'
              AND date_from <= ?
              AND date_to >= ?
            """,
            (today, today),
        )
        rows = [dict(row) for row in cur.fetchall()]
        _perf_log("list_leave_active_for_date", start, f"rows={len(rows)}")
        return rows
    finally:
        conn.close()


def _create_manual_request(
    employee: dict,
    date: str,
    time: str,
    action: str,
    reason: str,
    created_by: User,
) -> None:
    conn = _db_connect()
    try:
        conn.execute(
            """
            INSERT INTO manual_attendance_requests (
                employee_id, employee_name, employee_email,
                date, time, action, reason,
                created_by_user_id, created_by_email, created_by_role, created_at, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                employee.get("id"),
                employee.get("name"),
                employee.get("email"),
                date,
                time,
                action,
                reason,
                created_by.id,
                created_by.email,
                created_by.role,
                _now_ts(),
                "PENDING",
            ),
        )
    finally:
        conn.commit()
        conn.close()


def _manual_request_by_id(request_id: int) -> dict | None:
    conn = _db_connect()
    try:
        cur = conn.execute(
            "SELECT * FROM manual_attendance_requests WHERE id = ?",
            (request_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def _fetch_manual_requests(status: str, user: User | None = None) -> list[dict]:
    start = time.perf_counter()
    conn = _db_connect()
    try:
        status_key = status.upper()
        scope = _approver_scope_emails(user)
        if scope is not None:
            if not scope:
                return []
            placeholders = ",".join("?" for _ in scope)
            params = [status_key, *sorted(scope)]
            query = f"""
                SELECT *
                FROM manual_attendance_requests
                WHERE status = ?
                  AND lower(employee_email) IN ({placeholders})
                ORDER BY
                    CASE created_by_role
                        WHEN 'supervisor' THEN 1
                        WHEN 'manager_operational' THEN 2
                        ELSE 3
                    END,
                    created_at DESC
            """
            cur = conn.execute(query, params)
        else:
            cur = conn.execute(
                """
                SELECT *
                FROM manual_attendance_requests
                WHERE status = ?
                ORDER BY
                    CASE created_by_role
                        WHEN 'supervisor' THEN 1
                        WHEN 'manager_operational' THEN 2
                        ELSE 3
                    END,
                    created_at DESC
                """,
                (status_key,),
            )
        rows = [dict(row) for row in cur.fetchall()]
        _perf_log("fetch_manual_requests", start, f"status={status_key} rows={len(rows)}")
        return rows
    finally:
        conn.close()


def _approve_manual_request(request_id: int, reviewer: User, note: str | None) -> None:
    conn = _db_connect()
    try:
        conn.execute(
            """
            UPDATE manual_attendance_requests
            SET status = ?, reviewed_by_user_id = ?, reviewed_at = ?, review_note = ?
            WHERE id = ?
            """,
            ("APPROVED", reviewer.email, _now_ts(), note, request_id),
        )
    finally:
        conn.commit()
        conn.close()







def _approve_manual_request_atomic(
    request_id: int,
    reviewer: User,
    note: str | None,
) -> tuple[bool, str]:
    conn = _db_connect()
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT * FROM manual_attendance_requests WHERE id = ?",
            (request_id,),
        ).fetchone()
        if not row:
            conn.rollback()
            return False, "Data manual attendance tidak ditemukan."
        if row["status"] != "PENDING":
            conn.rollback()
            return False, "Manual attendance sudah diproses."
        exists = conn.execute(
            """
            SELECT 1 FROM attendance
            WHERE employee_email = ? AND date = ? AND action = ?
            LIMIT 1
            """,
            (row["employee_email"], row["date"], row["action"]),
        ).fetchone()
        if exists:
            conn.rollback()
            return False, "Attendance harian sudah tercatat."
        conn.execute(
            "UPDATE manual_attendance_requests SET status = ?, reviewed_by_user_id = ?, reviewed_at = ?, review_note = ? WHERE id = ?",
            ("APPROVED", reviewer.email, _now_ts(), note, request_id),
        )
        conn.execute(
            "INSERT INTO attendance (employee_id, employee_name, employee_email, date, time, action, method, selfie_path, source, manual_request_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                row["employee_id"],
                row["employee_name"],
                row["employee_email"],
                row["date"],
                row["time"],
                row["action"],
                "manual",
                None,
                "manual_request",
                row["id"],
                _now_ts(),
            ),
        )
        conn.commit()
        return True, ""
    except sqlite3.IntegrityError:
        conn.rollback()
        return False, "Attendance harian sudah tercatat."
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _employee_conflict(
    email: str,
    nik: str,
    no_hp: str,
    exclude_id: int | None = None,
) -> str | None:
    conn = _db_connect()
    try:
        if not _table_exists(conn, "employees"):
            return None
        params = {"exclude_id": exclude_id or 0}
        if email:
            row = conn.execute(
                """
                SELECT id FROM employees
                WHERE lower(email) = ? AND id != ?
                LIMIT 1
                """,
                (email.lower(), params["exclude_id"]),
            ).fetchone()
            if row:
                return "Email pegawai sudah terdaftar."
        if nik:
            row = conn.execute(
                """
                SELECT id FROM employees
                WHERE nik = ? AND id != ?
                LIMIT 1
                """,
                (nik, params["exclude_id"]),
            ).fetchone()
            if row:
                return "NIK pegawai sudah terdaftar."
        normalized = _normalize_phone(no_hp)
        if normalized:
            cur = conn.execute(
                """
                SELECT id, no_hp
                FROM employees
                WHERE id != ?
                """,
                (params["exclude_id"],),
            )
            for row in cur.fetchall():
                if _normalize_phone(row["no_hp"]) == normalized:
                    return "No telp pegawai sudah terdaftar."
        return None
    finally:
        conn.close()


def _reject_manual_request(request_id: int, reviewer: User, note: str) -> None:
    conn = _db_connect()
    try:
        conn.execute(
            """
            UPDATE manual_attendance_requests
            SET status = ?, reviewed_by_user_id = ?, reviewed_at = ?, review_note = ?
            WHERE id = ?
            """,
            ("REJECTED", reviewer.email, _now_ts(), note, request_id),
        )
    finally:
        conn.commit()
        conn.close()


def _insert_manual_attendance_record(request_row: dict) -> None:
    conn = _db_connect()
    try:
        conn.execute(
            """
            INSERT INTO attendance (
                employee_id, employee_name, employee_email,
                date, time, action, method, selfie_path, source, manual_request_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                request_row.get("employee_id"),
                request_row.get("employee_name"),
                request_row.get("employee_email"),
                request_row.get("date"),
                request_row.get("time"),
                request_row.get("action"),
                "manual",
                None,
                "manual_request",
                request_row.get("id"),
                _now_ts(),
            ),
        )
    finally:
        conn.commit()
        conn.close()


def _create_attendance_record(
    employee: dict | None,
    employee_email: str,
    action: str,
    method: str,
    device_time: str | None,
    source: str,
    selfie_path: str | None = None,
) -> dict:
    # Gunakan tanggal hari ini untuk field 'date', time dari device_time jika ada
    _, time_value = _device_time_parts(device_time)
    date_value = _today_key()
    employee_id = employee.get("id") if employee else None
    employee_name = employee.get("name") if employee else None
    created_at = _now_ts()
    print(f"[API] INSERT attendance: email={employee_email}, date={date_value}, time={time_value}, action={action}, method={method}, device_time={device_time}, source={source}, selfie_path={selfie_path}, created_at={created_at}")
    conn = _db_connect()
    try:
        cur = conn.execute(
            """
            INSERT INTO attendance (
                employee_id, employee_name, employee_email,
                date, time, action, method, selfie_path, source, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                employee_id,
                employee_name,
                employee_email,
                date_value,
                time_value,
                action,
                method,
                selfie_path,
                source,
                created_at,
            ),
        )
        record_id = int(cur.lastrowid)
    finally:
        conn.commit()
        conn.close()
    return {
        "id": record_id,
        "employee_email": employee_email,
        "action": action,
        "method": method,
        "date": date_value,
        "time": time_value,
        "created_at": created_at,
    }


def _list_attendance_today(employee_email: str, today: str, limit: int = 10) -> list[dict]:
    conn = _db_connect()
    try:
        if not _table_exists(conn, "attendance"):
            print(f"[API] Table 'attendance' does not exist!")
            return []
        print(f"[API] Querying attendance for email={employee_email}, date={today}, limit={limit}")
        cur = conn.execute(
            """
            SELECT id, employee_email, date, time, action, method, created_at
            FROM attendance
            WHERE employee_email = ? AND date = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (employee_email, today, limit),
        )
        rows = cur.fetchall()
        print(f"[API] Query result rows: {rows}")
        return [dict(row) for row in rows]
    finally:
        conn.close()


def _attendance_action_exists(
    employee_email: str,
    date_value: str,
    action: str,
    source: str | None = None,
) -> bool:
    conn = _db_connect()
    try:
        if not _table_exists(conn, "attendance"):
            return False
        clause = ""
        params = [employee_email, date_value, action]
        if source is not None:
            clause = "AND source = ?"
            params.append(source)
        query = (
            "SELECT 1 "
            "FROM attendance "
            "WHERE employee_email = ? AND date = ? AND action = ? "
            + clause + " "
            "LIMIT 1"
        )
        cur = conn.execute(query, tuple(params))
        return cur.fetchone() is not None
    finally:
        conn.close()


def _attendance_today_count(today: str) -> int:
    conn = _db_connect()
    try:
        if not _table_exists(conn, "attendance"):
            return 0
        cur = conn.execute(
            """
            SELECT COUNT(1) AS total
            FROM attendance
            WHERE date = ? AND action = 'checkin'
            """,
            (today,),
        )
        row = cur.fetchone()
        return int(row["total"]) if row else 0
    finally:
        conn.close()


def _attendance_today_count_for_emails(today: str, emails: set[str]) -> int:
    if not emails:
        return 0
    conn = _db_connect()
    try:
        if not _table_exists(conn, "attendance"):
            return 0
        placeholders = ",".join("?" for _ in emails)
        params = [today, *sorted({e.lower() for e in emails if e})]
        query = f"""
            SELECT COUNT(DISTINCT lower(employee_email)) AS total
            FROM attendance
            WHERE date = ? AND action = 'checkin'
              AND lower(employee_email) IN ({placeholders})
        """
        cur = conn.execute(query, params)
        row = cur.fetchone()
        return int(row["total"]) if row else 0
    finally:
        conn.close()


def _within_radius(lat: float, lng: float) -> bool:
    center_lat, center_lng = DEMO_GPS_CENTER
    radius_m = DEMO_GPS_RADIUS_METERS
    # Haversine distance in meters
    r = 6371000
    phi1 = math.radians(center_lat)
    phi2 = math.radians(lat)
    dphi = math.radians(lat - center_lat)
    dlambda = math.radians(lng - center_lng)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return (r * c) <= radius_m


def _within_site_radius(lat: float, lng: float, site: sqlite3.Row | dict | None) -> bool:
    if not site:
        return _within_radius(lat, lng)
    center_lat = site.get("latitude") if isinstance(site, dict) else site["latitude"]
    center_lng = site.get("longitude") if isinstance(site, dict) else site["longitude"]
    radius_m = site.get("radius_meters") if isinstance(site, dict) else site["radius_meters"]
    if center_lat is None or center_lng is None or radius_m is None:
        return _within_radius(lat, lng)
    r = 6371000
    phi1 = math.radians(center_lat)
    phi2 = math.radians(lat)
    dphi = math.radians(lat - center_lat)
    dlambda = math.radians(lng - center_lng)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return (r * c) <= radius_m


def _qr_secret_for_client(client_id: int | None) -> str:
    base = (os.environ.get("QR_SECRET") or "").strip()
    if not base:
        return ""
    if not client_id:
        return base
    return hmac.new(base.encode("utf-8"), f"client:{client_id}".encode("utf-8"), hashlib.sha256).hexdigest()


def _qr_window_start(ts: int, window_seconds: int = QR_WINDOW_SECONDS) -> int:
    return (ts // window_seconds) * window_seconds


def _build_qr_payload(client_id: int | None, action: str) -> str:
    secret = _qr_secret_for_client(client_id)
    if not secret:
        raise ValueError("QR secret tidak tersedia.")
    action_norm = action.upper().strip()
    now_ts = int(datetime.now(timezone.utc).timestamp())
    window_ts = _qr_window_start(now_ts)
    nonce_src = f"{window_ts}|{action_norm}|{client_id or 0}"
    nonce = hmac.new(secret.encode("utf-8"), nonce_src.encode("utf-8"), hashlib.sha256).hexdigest()[:12]
    data = f"{window_ts}|{nonce}|{action_norm}".encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), data, hashlib.sha256).hexdigest()
    return f"{DEMO_QR_PREFIX}|{window_ts}|{nonce}|{action_norm}|{sig}"


def _qr_image_base64(payload: str) -> str:
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _validate_qr_data(
    qr_data: str,
    client_id: int | None = None,
    action: str | None = None,
) -> tuple[bool, str]:
    payload = (qr_data or "").strip()
    if not payload:
        return False, "QR code wajib di-scan."
    secret = _qr_secret_for_client(client_id)
    if not secret:
        return False, "QR tidak dapat diverifikasi."
    parts = payload.split("|")
    if len(parts) not in {4, 5}:
        return False, "QR tidak valid."
    if len(parts) == 4:
        prefix, ts_raw, nonce, sig = parts
        action_raw = ""
    else:
        prefix, ts_raw, nonce, action_raw, sig = parts
    if prefix.upper() != DEMO_QR_PREFIX:
        return False, "QR tidak dikenali."
    if not ts_raw.isdigit():
        return False, "QR tidak valid."
    ts = int(ts_raw)
    now = int(datetime.now(timezone.utc).timestamp())
    if abs(now - ts) > QR_WINDOW_SECONDS:
        return False, "QR kadaluarsa."
    data_parts = [ts_raw, nonce]
    if action_raw:
        data_parts.append(action_raw.upper())
    data = "|".join(data_parts).encode("utf-8")
    expected = hmac.new(secret.encode("utf-8"), data, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return False, "QR tidak valid."
    if action and action_raw and action_raw.upper() != action.upper():
        return False, "QR tidak sesuai aksi."
    return True, "ok"


def admin_bp() -> Blueprint:
    bp = Blueprint("admin", __name__, url_prefix="/dashboard/admin")

    @bp.before_request
    def _guard():
        user = _current_user()
        if not user:
            return redirect(url_for("index"))
        if user.role not in ADMIN_ROLES:
            return redirect(url_for("dashboard_employee"))
        if user.role == "client_admin" and not _client_admin_client_id(user):
            return abort(403)
        if user.role != "hr_superadmin":
            permission = _permission_for_admin_endpoint(request.endpoint)
            if permission and not _has_role_permission(user.role, permission):
                return abort(403)

    @bp.route("/", methods=["GET"])
    def overview():
        user = _current_user()
        today = _today_key()
        client_scope = _client_admin_client_id(user)
        if client_scope:
            client_row = _get_client_by_id(client_scope)
            clients = [dict(client_row)] if client_row else []
            sites = _list_sites_by_client(client_scope)
            assignments = [
                a
                for a in _list_active_assignments(today)
                if int(a.get("client_id") or 0) == client_scope
            ]
            employee_ids = {
                int(a.get("employee_user_id") or 0)
                for a in assignments
                if a.get("employee_user_id")
            }
            employee_emails = {
                (a.get("employee_email") or "").lower()
                for a in assignments
                if a.get("employee_email")
            }
            stats = {
                "clients": len(clients),
                "employees": len(employee_ids),
                "attendance_today": _attendance_today_count_for_emails(today, employee_emails),
            }
        else:
            clients = _clients()
            stats = {
                "clients": len(clients),
                "employees": len(_employees()),
                "attendance_today": _attendance_today_count(today),
            }
            sites = _list_sites()
        primary_site = next((s for s in sites if s.get("is_active")), sites[0] if sites else None)
        site_name = primary_site["name"] if primary_site else "Belum ada site"
        site_client = primary_site.get("client_name") if primary_site else None
        site_meta_label = f"Client: {site_client}" if site_client else "Client: -"
        coords_value = "-"
        if primary_site:
            lat_raw = primary_site.get("latitude")
            lon_raw = primary_site.get("longitude")
            try:
                lat_val = float(lat_raw) if lat_raw is not None else None
                lon_val = float(lon_raw) if lon_raw is not None else None
            except (TypeError, ValueError):
                lat_val = lon_val = None
            if lat_val is not None and lon_val is not None:
                coords_value = f"{lat_val:.6f}, {lon_val:.6f}"
        shifts = _list_shifts()
        shift_target = next((s for s in shifts if s.get("is_active")), shifts[0] if shifts else None)
        shift_label = shift_target["name"] if shift_target else "Belum ada shift"
        shift_meta = f"{len(shifts)} shift terdaftar" if shifts else "Belum ada shift terdaftar"
        absent_count = stats["employees"] - stats["attendance_today"]
        if absent_count < 0:
            absent_count = 0
        kpi_cards = [
            {
                "label": "Client aktif",
                "value": stats["clients"],
                "meta": "Klien terdaftar",
                "theme": "slate",
            },
            {
                "label": "Jumlah Project",
                "value": len(sites),
                "meta": "Total site terdaftar",
                "theme": "amber",
            },
            {
                "label": "Koordinat",
                "value": coords_value,
                "meta": "Latitude · Longitude",
                "theme": "violet",
            },
            {
                "label": "Total Pegawai",
                "value": stats["employees"],
                "meta": "Pegawai aktif",
                "theme": "teal",
            },
            {
                "label": "Pegawai hadir",
                "value": stats["attendance_today"],
                "meta": "Check-in hari ini",
                "theme": "indigo",
            },
            {
                "label": "Pegawai absent",
                "value": absent_count,
                "meta": "Belum hadir",
                "theme": "rose",
            },
        ]
        client_summaries = _client_operational_summary(today, user, clients=clients)
        alerts = _build_admin_alerts(today, client_id=client_scope)
        audit_logs = [] if client_scope else _fetch_audit_logs(5)
        return render_template(
            "dashboard/admin_overview.html",
            user=user,
            stats=stats,
            client_summaries=client_summaries,
            alerts=alerts,
            kpi_cards=kpi_cards,
            audit_logs=audit_logs,
        )

    @bp.route("/qr", methods=["GET"])
    def qr_page():
        user = _current_user()
        client_scope = _client_admin_client_id(user)
        if client_scope:
            client_row = _get_client_by_id(client_scope)
            clients = [dict(client_row)] if client_row else []
        else:
            clients = _clients()
        selected_client_id = request.args.get("client_id")
        return render_template(
            "dashboard/admin_qr.html",
            user=user,
            clients=clients,
            selected_client_id=selected_client_id,
        )

    @bp.route("/qr/payload", methods=["GET"])
    def qr_payload():
        user = _current_user()
        if not user:
            return jsonify(ok=False, message="Unauthorized."), 403
        client_id = int(request.args.get("client_id") or 0) or None
        if user.role == "client_admin":
            _require_client_admin_client(user, client_id)
        if client_id:
            client = _get_client_by_id(client_id)
            if not client:
                return jsonify(ok=False, message="Client tidak ditemukan."), 404
        try:
            payload_in = _build_qr_payload(client_id, "IN")
            payload_out = _build_qr_payload(client_id, "OUT")
        except ValueError as err:
            return jsonify(ok=False, message=str(err)), 400
        now_ts = int(datetime.now(timezone.utc).timestamp())
        window_start = _qr_window_start(now_ts)
        window_end = window_start + QR_WINDOW_SECONDS
        image_in = _qr_image_base64(payload_in)
        image_out = _qr_image_base64(payload_out)
        return jsonify(
            ok=True,
            data={
                "payload_in": payload_in,
                "payload_out": payload_out,
                "image_in": image_in,
                "image_out": image_out,
                "window_start": window_start,
                "window_end": window_end,
                "server_ts": now_ts,
            },
        )

    @bp.route("/clients", methods=["GET"])
    def clients():
        user = _current_user()
        permissions = _get_role_permissions(user.role)
        client_scope = _client_admin_client_id(user)
        if client_scope:
            client_row = _get_client_by_id(client_scope)
            client_list = [dict(client_row)] if client_row else []
        else:
            client_list = _clients()
        return render_template(
            "dashboard/admin_clients.html",
            user=user,
            clients=client_list,
            permissions=permissions,
        )

    @bp.route("/clients/<int:client_id>", methods=["GET"])
    def client_profile(client_id: int):
        user = _current_user()
        if user and user.role == "client_admin":
            _require_client_admin_client(user, client_id)
        client = _get_client_by_id(client_id)
        if not client:
            flash("Client tidak ditemukan.")
            return redirect(url_for("admin.clients"))
        sites = _list_sites_by_client(client_id)
        assignments = _list_assignments_by_client(client_id)
        policies = _list_policies_by_client(client_id)
        contacts = _list_client_contacts(client_id)
        today = _today_key()

        site_policy_ids = {
            int(p["site_id"])
            for p in policies
            if p.get("scope_type") == "SITE"
            and p.get("site_id")
            and _policy_active_for_date(p, today)
        }
        summary = {
            "sites_total": len(sites),
            "sites_active": len([s for s in sites if int(s.get("is_active") or 0) == 1]),
            "assignments_active": len(
                [
                    a
                    for a in assignments
                    if (a.get("status") == "ACTIVE")
                    and (a.get("start_date") or "") <= today
                    and (not a.get("end_date") or a.get("end_date") >= today)
                ]
            ),
            "client_policy_active": any(
                p.get("scope_type") == "CLIENT"
                and int(p.get("client_id") or 0) == client_id
                and _policy_active_for_date(p, today)
                for p in policies
            ),
            "site_policy_count": len(site_policy_ids),
        }
        return render_template(
            "dashboard/admin_client_profile.html",
            user=user,
            client=client,
            sites=sites,
            assignments=assignments,
            policies=policies,
            contacts=contacts,
            summary=summary,
        )

    @bp.route("/clients/<int:client_id>/contacts/create", methods=["POST"])
    def client_contacts_create(client_id: int):
        user = _current_user()
        if user and user.role == "client_admin":
            _require_client_admin_client(user, client_id)
        else:
            _require_hr_superadmin(user)
        if not _get_client_by_id(client_id):
            flash("Client tidak ditemukan.")
            return redirect(url_for("admin.clients"))
        contact_type = (request.form.get("contact_type") or "").strip().upper()
        name = (request.form.get("name") or "").strip()
        title = (request.form.get("title") or "").strip()
        phone = (request.form.get("phone") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        notes = (request.form.get("notes") or "").strip()
        is_primary = 1 if request.form.get("is_primary") == "1" else 0

        if contact_type not in {"OPERATIONAL", "BILLING", "HR", "OTHER"}:
            flash("Tipe PIC tidak valid.")
            return redirect(url_for("admin.client_profile", client_id=client_id))
        if not name:
            flash("Nama PIC wajib diisi.")
            return redirect(url_for("admin.client_profile", client_id=client_id))

        _create_client_contact(
            client_id=client_id,
            contact_type=contact_type,
            name=name,
            title=title or None,
            phone=phone or None,
            email=email or None,
            is_primary=is_primary,
            notes=notes or None,
        )
        flash("Kontak client ditambahkan.")
        return redirect(url_for("admin.client_profile", client_id=client_id))

    @bp.route("/clients/contacts/<int:contact_id>/primary", methods=["POST"])
    def client_contacts_primary(contact_id: int):
        user = _current_user()
        if user and user.role != "client_admin":
            _require_hr_superadmin(user)
        contact = _get_client_contact_by_id(contact_id)
        if not contact:
            flash("Kontak tidak ditemukan.")
            return redirect(url_for("admin.clients"))
        if user and user.role == "client_admin":
            _require_client_admin_client(user, contact.get("client_id"))
        _set_primary_client_contact(contact_id)
        flash("Primary PIC diperbarui.")
        return redirect(url_for("admin.client_profile", client_id=contact["client_id"]))

    @bp.route("/clients/contacts/<int:contact_id>/delete", methods=["POST"])
    def client_contacts_delete(contact_id: int):
        user = _current_user()
        if user and user.role != "client_admin":
            _require_hr_superadmin(user)
        contact = _get_client_contact_by_id(contact_id)
        if not contact:
            flash("Kontak tidak ditemukan.")
            return redirect(url_for("admin.clients"))
        if user and user.role == "client_admin":
            _require_client_admin_client(user, contact.get("client_id"))
        _delete_client_contact(contact_id)
        flash("Kontak client dihapus.")
        return redirect(url_for("admin.client_profile", client_id=contact["client_id"]))

    @bp.route("/sites", methods=["GET"])
    def sites():
        user = _current_user()
        client_scope = _client_admin_client_id(user)
        client_row = None
        if client_scope:
            client_row = _get_client_by_id(client_scope)
            sites = _list_sites_by_client(client_scope)
            orphan_sites = []
            today = _today_key()
            site_policy_ids, client_policy_ids = _active_policy_sets_for_client(
                today, client_scope
            )
            for site in sites:
                site["is_orphan"] = False
        else:
            sites = _list_sites()
            orphan_sites = [s for s in sites if s.get("is_orphan")]
            today = _today_key()
            site_policy_ids, client_policy_ids = _active_policy_sets(today)
        assignment_counts = _active_assignment_counts(today)
        for site in sites:
            score = 0
            if int(site.get("is_active") or 0) == 1:
                score += 1
            if assignment_counts.get(int(site.get("id") or 0), 0) > 0:
                score += 1
            client_id = site.get("client_id")
            has_policy = False
            if site.get("id") and int(site["id"]) in site_policy_ids:
                has_policy = True
            elif client_id and int(client_id) in client_policy_ids:
                has_policy = True
            if has_policy:
                score += 1
            if score == 3:
                label, cls = "Compliant", "approved"
            elif score == 2:
                label, cls = "Watch", "pending"
            else:
                label, cls = "Risk", "rejected"
            site["compliance_score"] = score
            site["compliance_label"] = label
            site["compliance_class"] = cls
        return render_template(
            "dashboard/admin_sites.html",
            user=user,
            clients=_clients() if not client_scope else [dict(client_row)] if client_row else [],
            sites=sites,
            orphan_sites=orphan_sites,
        )

    @bp.route("/assignments", methods=["GET"])
    def assignments():
        user = _current_user()
        client_scope = _client_admin_client_id(user)
        assignments = _list_assignments(client_id=client_scope) if client_scope else _list_assignments()
        return render_template(
            "dashboard/admin_assignments.html",
            user=user,
            employees=_list_employee_users(),
            sites=_list_sites_by_client(client_scope) if client_scope else _list_sites(),
            shifts=_list_shifts(),
            assignments=assignments,
        )

    @bp.route("/policies", methods=["GET"])
    def policies():
        user = _current_user()
        client_scope = _client_admin_client_id(user)
        client_row = _get_client_by_id(client_scope) if client_scope else None
        return render_template(
            "dashboard/admin_policies.html",
            user=user,
            clients=_clients() if not client_scope else [dict(client_row)] if client_row else [],
            sites=_list_sites_by_client(client_scope) if client_scope else _list_sites(),
            shifts=_list_shifts(),
            policies=_list_policies_by_client(client_scope) if client_scope else _list_policies(),
        )

    @bp.route("/shifts", methods=["GET"])
    def shifts():
        user = _current_user()
        return render_template(
            "dashboard/admin_shifts.html",
            user=user,
            shifts=_list_shifts(),
        )

    @bp.route("/clients/create", methods=["POST"])
    def clients_create():
        user = _current_user()
        _require_admin(user)
        if user and user.role == "client_admin":
            return abort(403)
        name = (request.form.get("client_name") or "").strip()
        legal_name = (request.form.get("legal_name") or "").strip()
        address = (request.form.get("address") or "").strip()
        office_email = (request.form.get("office_email") or "").strip()
        office_phone = (request.form.get("office_phone") or "").strip()
        pic_name = (request.form.get("pic_name") or "").strip()
        pic_title = (request.form.get("pic_title") or "").strip()
        pic_phone = (request.form.get("pic_phone") or "").strip()
        notes = (request.form.get("notes") or "").strip()
        if not name:
            flash("Nama client wajib diisi.")
            return redirect(url_for("admin.clients", _anchor="add-client"))
        if not address:
            flash("Alamat client wajib diisi.")
            return redirect(url_for("admin.clients", _anchor="add-client"))
        if not office_email:
            flash("Email kantor wajib diisi.")
            return redirect(url_for("admin.clients", _anchor="add-client"))
        if not office_phone:
            flash("No telp kantor wajib diisi.")
            return redirect(url_for("admin.clients", _anchor="add-client"))
        if not pic_name:
            flash("Nama PIC wajib diisi.")
            return redirect(url_for("admin.clients", _anchor="add-client"))
        if not pic_title:
            flash("Jabatan PIC wajib diisi.")
            return redirect(url_for("admin.clients", _anchor="add-client"))
        if not pic_phone:
            flash("No HP PIC wajib diisi.")
            return redirect(url_for("admin.clients", _anchor="add-client"))
        conflict = _find_client_identity_conflict(name, legal_name)
        if conflict:
            flash("Nama client atau nama legal sudah digunakan.")
            return redirect(url_for("admin.clients", _anchor="add-client"))
        _create_client(
            name=name,
            legal_name=legal_name or None,
            address=address,
            office_email=office_email,
            office_phone=office_phone,
            pic_name=pic_name,
            pic_title=pic_title,
            pic_phone=pic_phone,
            notes=notes or None,
        )
        flash("Client berhasil ditambahkan.")
        return redirect(url_for("admin.clients", _anchor="add-client"))

    @bp.route("/clients/<int:client_id>/update", methods=["POST"])
    def clients_update(client_id: int):
        user = _current_user()
        _require_admin(user)
        if user and user.role == "client_admin":
            _require_client_admin_client(user, client_id)
        client = _get_client_by_id(client_id)
        if not client:
            flash("Client tidak ditemukan.")
            return redirect(url_for("admin.clients"))
        name = (request.form.get("client_name") or "").strip()
        legal_name = (request.form.get("legal_name") or "").strip()
        address = (request.form.get("address") or "").strip()
        office_email = (request.form.get("office_email") or "").strip()
        office_phone = (request.form.get("office_phone") or "").strip()
        pic_name = (request.form.get("pic_name") or "").strip()
        pic_title = (request.form.get("pic_title") or "").strip()
        pic_phone = (request.form.get("pic_phone") or "").strip()
        notes = (request.form.get("notes") or "").strip()
        is_active = int(request.form.get("is_active") or 0)
        if not name:
            flash("Nama client wajib diisi.")
            return redirect(url_for("admin.clients"))
        if not address:
            flash("Alamat client wajib diisi.")
            return redirect(url_for("admin.clients"))
        if not office_email:
            flash("Email kantor wajib diisi.")
            return redirect(url_for("admin.clients"))
        if not office_phone:
            flash("No telp kantor wajib diisi.")
            return redirect(url_for("admin.clients"))
        if not pic_name:
            flash("Nama PIC wajib diisi.")
            return redirect(url_for("admin.clients"))
        if not pic_title:
            flash("Jabatan PIC wajib diisi.")
            return redirect(url_for("admin.clients"))
        if not pic_phone:
            flash("No HP PIC wajib diisi.")
            return redirect(url_for("admin.clients"))
        current_name = _normalize_client_identity(client["name"] if "name" in client.keys() else None) or ""
        current_legal = _normalize_client_identity(client["legal_name"] if "legal_name" in client.keys() else None) or ""
        next_name = _normalize_client_identity(name) or ""
        next_legal = _normalize_client_identity(legal_name) or ""
        identity_changed = (
            current_name.lower() != next_name.lower()
            or current_legal.lower() != next_legal.lower()
        )
        if identity_changed:
            conflict = _find_client_identity_conflict(
                name, legal_name, exclude_client_id=client_id
            )
            if conflict:
                flash("Nama client atau nama legal sudah digunakan.")
                return redirect(url_for("admin.clients"))
        _update_client(
            client_id=client_id,
            name=name,
            legal_name=legal_name or None,
            address=address,
            office_email=office_email,
            office_phone=office_phone,
            pic_name=pic_name,
            pic_title=pic_title,
            pic_phone=pic_phone,
            is_active=is_active,
            notes=notes or None,
        )
        flash("Client berhasil diperbarui.")
        return redirect(url_for("admin.clients"))

    @bp.route("/clients/<int:client_id>/delete", methods=["POST"])
    def clients_delete(client_id: int):
        user = _current_user()
        _require_admin(user)
        if user and user.role == "client_admin":
            return abort(403)
        if _client_has_sites(client_id):
            flash("Client masih punya site. Pindahkan atau hapus site terlebih dahulu.")
            return redirect(url_for("admin.clients"))
        _delete_client(client_id)
        flash("Client berhasil dihapus.")
        return redirect(url_for("admin.clients"))

    @bp.route("/assignments/create", methods=["POST"])
    def assignments_create():
        user = _current_user()
        _require_hr_or_client_admin(user)
        employee_id_raw = (request.form.get("employee_user_id") or "").strip()
        site_id_raw = (request.form.get("site_id") or "").strip()
        shift_id_raw = (request.form.get("shift_id") or "").strip()
        job_title = (request.form.get("job_title") or "").strip()
        start_date = (request.form.get("start_date") or "").strip()
        end_date = (request.form.get("end_date") or "").strip()
        status = (request.form.get("status") or "ACTIVE").strip().upper()

        if not employee_id_raw or not site_id_raw:
            flash("Pegawai dan site wajib dipilih.")
            return redirect(url_for("admin.assignments", _anchor="add-assignment"))
        if not start_date:
            flash("Tanggal mulai wajib diisi.")
            return redirect(url_for("admin.assignments", _anchor="add-assignment"))
        try:
            employee_id = int(employee_id_raw)
            site_id = int(site_id_raw)
        except ValueError:
            flash("Pegawai atau site tidak valid.")
            return redirect(url_for("admin.assignments", _anchor="add-assignment"))
        if user and user.role == "client_admin":
            _require_client_admin_site(user, site_id)
        shift_id = None
        if shift_id_raw:
            if not shift_id_raw.isdigit():
                flash("Shift tidak valid.")
                return redirect(url_for("admin.assignments", _anchor="add-assignment"))
            shift_id = int(shift_id_raw)
            shift_row = _get_shift_by_id(shift_id)
            if not shift_row or int(shift_row["is_active"] or 0) != 1:
                flash("Shift tidak ditemukan atau nonaktif.")
                return redirect(url_for("admin.assignments", _anchor="add-assignment"))
        if status not in {"ACTIVE", "ENDED"}:
            status = "ACTIVE"

        normalized_start = _normalize_date_input(start_date)
        if not normalized_start:
            flash("Tanggal mulai wajib format DD-MM-YYYY (contoh 01-02-2026) atau 1 Feb 2026.")
            return redirect(url_for("admin.assignments", _anchor="add-assignment"))
        normalized_end = _normalize_date_input(end_date) if end_date else None
        if end_date and not normalized_end:
            flash("Tanggal selesai wajib format DD-MM-YYYY (contoh 01-02-2026) atau 1 Feb 2026.")
            return redirect(url_for("admin.assignments", _anchor="add-assignment"))

        assignment_id = _create_assignment_with_log(
            actor=user,
            employee_user_id=employee_id,
            site_id=site_id,
            shift_id=shift_id,
            job_title=job_title or None,
            start_date=normalized_start,
            end_date=normalized_end,
            status=status,
            summary=f"Assignment dibuat untuk user_id {employee_id} ke site_id {site_id}.",
            portal="admin_dashboard",
        )
        flash("Assignment berhasil ditambahkan.")
        return redirect(url_for("admin.assignments", _anchor="add-assignment"))

    @bp.route("/assignments/<int:assignment_id>/update", methods=["POST"])
    def assignments_update(assignment_id: int):
        user = _current_user()
        _require_hr_or_client_admin(user)
        employee_id_raw = (request.form.get("employee_user_id") or "").strip()
        site_id_raw = (request.form.get("site_id") or "").strip()
        shift_id_raw = (request.form.get("shift_id") or "").strip()
        job_title = (request.form.get("job_title") or "").strip()
        start_date = (request.form.get("start_date") or "").strip()
        end_date = (request.form.get("end_date") or "").strip()
        status = (request.form.get("status") or "ACTIVE").strip().upper()

        if not employee_id_raw or not site_id_raw:
            flash("Pegawai dan site wajib dipilih.")
            return redirect(url_for("admin.assignments"))
        if not start_date:
            flash("Tanggal mulai wajib diisi.")
            return redirect(url_for("admin.assignments"))
        try:
            employee_id = int(employee_id_raw)
            site_id = int(site_id_raw)
        except ValueError:
            flash("Pegawai atau site tidak valid.")
            return redirect(url_for("admin.assignments"))
        if user and user.role == "client_admin":
            _require_client_admin_site(user, site_id)
        shift_id = None
        if shift_id_raw:
            if not shift_id_raw.isdigit():
                flash("Shift tidak valid.")
                return redirect(url_for("admin.assignments"))
            shift_id = int(shift_id_raw)
            shift_row = _get_shift_by_id(shift_id)
            if not shift_row or int(shift_row["is_active"] or 0) != 1:
                flash("Shift tidak ditemukan atau nonaktif.")
                return redirect(url_for("admin.assignments"))
        if status not in {"ACTIVE", "ENDED"}:
            status = "ACTIVE"

        normalized_start = _normalize_date_input(start_date)
        if not normalized_start:
            flash("Tanggal mulai wajib format DD-MM-YYYY (contoh 01-02-2026) atau 1 Feb 2026.")
            return redirect(url_for("admin.assignments"))
        normalized_end = _normalize_date_input(end_date) if end_date else None
        if end_date and not normalized_end:
            flash("Tanggal selesai wajib format DD-MM-YYYY (contoh 01-02-2026) atau 1 Feb 2026.")
            return redirect(url_for("admin.assignments"))

        current = _get_assignment_by_id(assignment_id)
        if not current:
            flash("Assignment tidak ditemukan.")
            return redirect(url_for("admin.assignments"))
        if user and user.role == "client_admin":
            _require_client_admin_site(user, current.get("site_id"))

        if status == "ACTIVE":
            current_status = (current.get("status") or "").upper()
            current_employee_id = int(current.get("employee_user_id") or 0)
            current_site_id = int(current.get("site_id") or 0)
            current_shift_id = current.get("shift_id")
            current_shift_id = int(current_shift_id) if current_shift_id not in (None, "") else None
            current_start_date_raw = (current.get("start_date") or "").strip()
            current_start_date = _normalize_date_input(current_start_date_raw) or current_start_date_raw
            needs_new = current_status != "ACTIVE"
            if not needs_new:
                if (
                    current_employee_id != employee_id
                    or current_site_id != site_id
                    or current_shift_id != shift_id
                    or current_start_date != normalized_start
                ):
                    needs_new = True
            if needs_new:
                if current_status == "ACTIVE":
                    _end_assignment_with_date(assignment_id, normalized_start)
                    _log_audit_event(
                        entity_type="assignment",
                        entity_id=assignment_id,
                        action="END",
                        actor=user,
                        summary=f"Assignment ditutup untuk user_id {current_employee_id}.",
                        details={
                            "before": current,
                            "end_date": normalized_start,
                        },
                    )
                new_assignment_id = _create_assignment_with_log(
                    actor=user,
                    employee_user_id=employee_id,
                    site_id=site_id,
                    shift_id=shift_id,
                    job_title=job_title or None,
                    start_date=normalized_start,
                    end_date=normalized_end,
                    status=status,
                    summary=f"Assignment baru dibuat untuk user_id {employee_id} ke site_id {site_id}.",
                    portal="admin_dashboard",
                    extra_details={"previous_assignment_id": assignment_id},
                )
                flash("Assignment baru dibuat (history tersimpan).")
                return redirect(url_for("admin.assignments"))

        _update_assignment(
            assignment_id=assignment_id,
            employee_user_id=employee_id,
            site_id=site_id,
            shift_id=shift_id,
            job_title=job_title or None,
            start_date=normalized_start,
            end_date=normalized_end,
            status=status,
        )
        _log_audit_event(
            entity_type="assignment",
            entity_id=assignment_id,
            action="UPDATE",
            actor=user,
            summary=f"Assignment diperbarui untuk user_id {employee_id}.",
            details={
                "before": current,
                "after": {
                    "employee_user_id": employee_id,
                    "site_id": site_id,
                    "shift_id": shift_id,
                    "job_title": job_title or None,
                    "start_date": normalized_start,
                    "end_date": normalized_end,
                    "status": status,
                },
            },
        )
        flash("Assignment berhasil diperbarui.")
        return redirect(url_for("admin.assignments"))

    @bp.route("/assignments/<int:assignment_id>/end", methods=["POST"])
    def assignments_end(assignment_id: int):
        user = _current_user()
        _require_hr_or_client_admin(user)
        current = _get_assignment_by_id(assignment_id)
        if user and user.role == "client_admin":
            _require_client_admin_site(user, current.get("site_id") if current else None)
        _end_assignment(assignment_id)
        _log_audit_event(
            entity_type="assignment",
            entity_id=assignment_id,
            action="END",
            actor=user,
            summary=f"Assignment ditutup untuk id {assignment_id}.",
            details={
                "before": current,
                "end_date": _today_key(),
            },
        )
        flash("Assignment ditutup.")
        return redirect(url_for("admin.assignments"))

    @bp.route("/assignments/<int:assignment_id>/delete", methods=["POST"])
    def assignments_delete(assignment_id: int):
        user = _current_user()
        _require_hr_or_client_admin(user)
        current = _get_assignment_by_id(assignment_id)
        if not current:
            flash("Assignment tidak ditemukan.")
            return redirect(url_for("admin.assignments"))
        if user and user.role == "client_admin":
            _require_client_admin_site(user, current.get("site_id"))
        _delete_assignment(assignment_id)
        _log_audit_event(
            entity_type="assignment",
            entity_id=assignment_id,
            action="DELETE",
            actor=user,
            summary=f"Assignment dihapus untuk id {assignment_id}.",
            details={"before": current},
        )
        flash("Assignment dihapus.")
        return redirect(url_for("admin.assignments"))

    @bp.route("/policies/create", methods=["POST"])
    def policies_create():
        user = _current_user()
        _require_hr_or_client_admin(user)
        scope_type = (request.form.get("scope_type") or "CLIENT").strip().upper()
        client_id_raw = (request.form.get("client_id") or "").strip()
        site_id_raw = (request.form.get("site_id") or "").strip()
        shift_id_raw = (request.form.get("shift_id") or "").strip()
        effective_from = (request.form.get("effective_from") or "").strip()
        effective_to = (request.form.get("effective_to") or "").strip()
        work_duration_raw = (request.form.get("work_duration_minutes") or "").strip()
        grace_raw = (request.form.get("grace_minutes") or "").strip()
        allow_gps = 1 if request.form.get("allow_gps") == "1" else 0
        require_selfie = 1 if request.form.get("require_selfie") == "1" else 0
        allow_qr = 1 if request.form.get("allow_qr") == "1" else 0
        auto_checkout = 1 if request.form.get("auto_checkout") == "1" else 0
        cutoff_time = (request.form.get("cutoff_time") or "").strip()

        if scope_type not in {"CLIENT", "SITE"}:
            scope_type = "CLIENT"
        if not effective_from:
            flash("Tanggal mulai wajib diisi.")
            return redirect(url_for("admin.policies", _anchor="add-policy"))

        client_id = int(client_id_raw) if client_id_raw.isdigit() else None
        site_id = int(site_id_raw) if site_id_raw.isdigit() else None
        if scope_type == "CLIENT" and not client_id:
            flash("Client wajib dipilih untuk scope CLIENT.")
            return redirect(url_for("admin.policies", _anchor="add-policy"))
        if scope_type == "SITE" and not site_id:
            flash("Site wajib dipilih untuk scope SITE.")
            return redirect(url_for("admin.policies", _anchor="add-policy"))
        if user and user.role == "client_admin":
            if scope_type == "CLIENT":
                _require_client_admin_client(user, client_id)
            else:
                _require_client_admin_site(user, site_id)

        shift_id = None
        if shift_id_raw:
            if not shift_id_raw.isdigit():
                flash("Shift tidak valid.")
                return redirect(url_for("admin.policies", _anchor="add-policy"))
            shift_id = int(shift_id_raw)
            shift_row = _get_shift_by_id(shift_id)
            if not shift_row or int(shift_row["is_active"] or 0) != 1:
                flash("Shift tidak ditemukan atau nonaktif.")
                return redirect(url_for("admin.policies", _anchor="add-policy"))

        work_duration = int(work_duration_raw) if work_duration_raw.isdigit() else None
        grace_minutes = int(grace_raw) if grace_raw.isdigit() else None
        late_minutes = None

        policy_id = _create_policy(
            scope_type=scope_type,
            client_id=client_id,
            site_id=site_id,
            shift_id=shift_id,
            effective_from=effective_from,
            effective_to=effective_to or None,
            work_duration_minutes=work_duration,
            grace_minutes=grace_minutes,
            late_threshold_minutes=late_minutes,
            allow_gps=allow_gps,
            require_selfie=require_selfie,
            allow_qr=allow_qr,
            auto_checkout=auto_checkout,
            cutoff_time=cutoff_time or None,
        )
        _log_audit_event(
            entity_type="policy",
            entity_id=policy_id,
            action="CREATE",
            actor=user,
            summary=f"Policy dibuat untuk scope {scope_type}.",
            details={
                "scope_type": scope_type,
                "client_id": client_id,
                "site_id": site_id,
                "shift_id": shift_id,
                "effective_from": effective_from,
                "effective_to": effective_to or None,
                "work_duration_minutes": work_duration,
                "grace_minutes": grace_minutes,
                "late_threshold_minutes": late_minutes,
                "allow_gps": allow_gps,
                "require_selfie": require_selfie,
                "allow_qr": allow_qr,
                "auto_checkout": auto_checkout,
                "cutoff_time": cutoff_time or None,
            },
        )
        flash("Policy berhasil ditambahkan.")
        return redirect(url_for("admin.policies", _anchor="add-policy"))

    @bp.route("/policies/<int:policy_id>/update", methods=["POST"])
    def policies_update(policy_id: int):
        user = _current_user()
        _require_hr_or_client_admin(user)
        before = _get_policy_by_id(policy_id)
        scope_type = (request.form.get("scope_type") or "CLIENT").strip().upper()
        client_id_raw = (request.form.get("client_id") or "").strip()
        site_id_raw = (request.form.get("site_id") or "").strip()
        shift_id_raw = (request.form.get("shift_id") or "").strip()
        effective_from = (request.form.get("effective_from") or "").strip()
        effective_to = (request.form.get("effective_to") or "").strip()
        work_duration_raw = (request.form.get("work_duration_minutes") or "").strip()
        grace_raw = (request.form.get("grace_minutes") or "").strip()
        allow_gps = 1 if request.form.get("allow_gps") == "1" else 0
        require_selfie = 1 if request.form.get("require_selfie") == "1" else 0
        allow_qr = 1 if request.form.get("allow_qr") == "1" else 0
        auto_checkout = 1 if request.form.get("auto_checkout") == "1" else 0
        cutoff_time = (request.form.get("cutoff_time") or "").strip()

        if scope_type not in {"CLIENT", "SITE"}:
            scope_type = "CLIENT"
        if not effective_from:
            flash("Tanggal mulai wajib diisi.")
            return redirect(url_for("admin.policies"))

        client_id = int(client_id_raw) if client_id_raw.isdigit() else None
        site_id = int(site_id_raw) if site_id_raw.isdigit() else None
        if scope_type == "CLIENT" and not client_id:
            flash("Client wajib dipilih untuk scope CLIENT.")
            return redirect(url_for("admin.policies"))
        if scope_type == "SITE" and not site_id:
            flash("Site wajib dipilih untuk scope SITE.")
            return redirect(url_for("admin.policies"))
        if user and user.role == "client_admin":
            if before:
                before_scope = before.get("scope_type")
                if before_scope == "CLIENT":
                    _require_client_admin_client(user, before.get("client_id"))
                elif before_scope == "SITE":
                    _require_client_admin_site(user, before.get("site_id"))
            if scope_type == "CLIENT":
                _require_client_admin_client(user, client_id)
            else:
                _require_client_admin_site(user, site_id)

        shift_id = None
        if shift_id_raw:
            if not shift_id_raw.isdigit():
                flash("Shift tidak valid.")
                return redirect(url_for("admin.policies"))
            shift_id = int(shift_id_raw)
            shift_row = _get_shift_by_id(shift_id)
            if not shift_row or int(shift_row["is_active"] or 0) != 1:
                flash("Shift tidak ditemukan atau nonaktif.")
                return redirect(url_for("admin.policies"))

        work_duration = int(work_duration_raw) if work_duration_raw.isdigit() else None
        grace_minutes = int(grace_raw) if grace_raw.isdigit() else None
        late_minutes = None if not before else before.get("late_threshold_minutes")

        _update_policy(
            policy_id=policy_id,
            scope_type=scope_type,
            client_id=client_id,
            site_id=site_id,
            shift_id=shift_id,
            effective_from=effective_from,
            effective_to=effective_to or None,
            work_duration_minutes=work_duration,
            grace_minutes=grace_minutes,
            late_threshold_minutes=late_minutes,
            allow_gps=allow_gps,
            require_selfie=require_selfie,
            allow_qr=allow_qr,
            auto_checkout=auto_checkout,
            cutoff_time=cutoff_time or None,
        )
        _log_audit_event(
            entity_type="policy",
            entity_id=policy_id,
            action="UPDATE",
            actor=user,
            summary=f"Policy diperbarui untuk scope {scope_type}.",
            details={
                "before": before,
                "after": {
                    "scope_type": scope_type,
                    "client_id": client_id,
                    "site_id": site_id,
                    "shift_id": shift_id,
                    "effective_from": effective_from,
                    "effective_to": effective_to or None,
                    "work_duration_minutes": work_duration,
                    "grace_minutes": grace_minutes,
                    "late_threshold_minutes": late_minutes,
                    "allow_gps": allow_gps,
                    "require_selfie": require_selfie,
                    "allow_qr": allow_qr,
                    "auto_checkout": auto_checkout,
                    "cutoff_time": cutoff_time or None,
                },
            },
        )
        flash("Policy berhasil diperbarui.")
        return redirect(url_for("admin.policies"))

    @bp.route("/policies/<int:policy_id>/end", methods=["POST"])
    def policies_end(policy_id: int):
        user = _current_user()
        _require_hr_or_client_admin(user)
        before = _get_policy_by_id(policy_id)
        if user and user.role == "client_admin":
            if before and before.get("scope_type") == "CLIENT":
                _require_client_admin_client(user, before.get("client_id"))
            elif before and before.get("scope_type") == "SITE":
                _require_client_admin_site(user, before.get("site_id"))
        _end_policy(policy_id)
        _log_audit_event(
            entity_type="policy",
            entity_id=policy_id,
            action="END",
            actor=user,
            summary=f"Policy ditutup untuk id {policy_id}.",
            details={
                "before": before,
                "effective_to": _today_key(),
            },
        )
        flash("Policy ditutup.")
        return redirect(url_for("admin.policies"))

    @bp.route("/policies/<int:policy_id>/delete", methods=["POST"])
    def policies_delete(policy_id: int):
        user = _current_user()
        _require_hr_or_client_admin(user)
        before = _get_policy_by_id(policy_id)
        if not before:
            flash("Policy tidak ditemukan.")
            return redirect(url_for("admin.policies"))
        if user and user.role == "client_admin":
            scope = before.get("scope_type")
            if scope == "CLIENT":
                _require_client_admin_client(user, before.get("client_id"))
            elif scope == "SITE":
                _require_client_admin_site(user, before.get("site_id"))
        _delete_policy(policy_id)
        _log_audit_event(
            entity_type="policy",
            entity_id=policy_id,
            action="DELETE",
            actor=user,
            summary=f"Policy dihapus untuk id {policy_id}.",
            details={"before": before},
        )
        flash("Policy berhasil dihapus.")
        return redirect(url_for("admin.policies"))

    @bp.route("/employees", methods=["GET"])
    def employees():
        user = _current_user()
        permissions = _get_role_permissions(user.role)
        employees = _employees()
        client_scope = _client_admin_client_id(user)
        if client_scope:
            today = _today_key()
            assignments = _list_active_assignments(today)
            scoped_emails = {
                (a.get("employee_email") or "").lower()
                for a in assignments
                if int(a.get("client_id") or 0) == client_scope
            }
            employees = [
                e
                for e in employees
                if (e.get("email") or "").lower() in scoped_emails
            ]
        return render_template(
            "dashboard/admin_employees.html",
            user=user,
            employees=employees,
            permissions=permissions,
        )

    @bp.route("/employees/create", methods=["POST"])
    def employees_create():
        user = _current_user()
        _require_hr_superadmin(user)
        payload, error = _parse_employee_form(request.form or {})
        if error:
            flash(error)
            return redirect(url_for("admin.employees", _anchor="add-employee"))
        conflict = _employee_conflict(payload["email"], payload["nik"], payload["no_hp"])
        if conflict:
            flash(conflict)
            return redirect(url_for("admin.employees", _anchor="add-employee"))
        _create_employee(
            nik=payload["nik"],
            name=payload["name"],
            email=payload["email"],
            no_hp=payload["no_hp"],
            address=payload["address"],
            gender=payload["gender"],
            status_nikah=payload["status_nikah"],
            notes=payload["notes"],
            is_active=0,
        )
        flash("Pegawai berhasil ditambahkan.")
        return redirect(url_for("admin.employees", _anchor="add-employee"))

    @bp.route("/employees/<int:employee_id>/update", methods=["POST"])
    def employees_update(employee_id: int):
        user = _current_user()
        _require_hr_superadmin(user)
        payload, error = _parse_employee_form(request.form or {})
        is_active = 1 if request.form.get("is_active") == "1" else 0
        if error:
            flash(error)
            return redirect(url_for("admin.employees"))
        conflict = _employee_conflict(
            payload["email"],
            payload["nik"],
            payload["no_hp"],
            exclude_id=employee_id,
        )
        if conflict:
            flash(conflict)
            return redirect(url_for("admin.employees"))
        _update_employee(
            employee_id=employee_id,
            nik=payload["nik"],
            name=payload["name"],
            email=payload["email"],
            no_hp=payload["no_hp"],
            address=payload["address"],
            gender=payload["gender"],
            status_nikah=payload["status_nikah"],
            notes=payload["notes"],
            is_active=is_active,
        )
        flash("Data pegawai berhasil diperbarui.")
        return redirect(url_for("admin.employees"))

    @bp.route("/employees/<int:employee_id>/delete", methods=["POST"])
    def employees_delete(employee_id: int):
        user = _current_user()
        _require_hr_superadmin(user)
        employee = _employee_by_id(employee_id)
        if not employee:
            flash("Pegawai tidak ditemukan.")
            return redirect(url_for("admin.employees"))
        employee_email = employee.get("email") or ""
        user_row = _get_user_by_email(employee_email)
        employee_user_id = int(_row_get(user_row, "id") or 0) if user_row else 0
        deleted_assignments = 0
        if employee_user_id:
            deleted_assignments = _delete_assignments_for_employee(employee_user_id)
        _delete_employee(employee_id)
        _log_audit_event(
            entity_type="employee",
            entity_id=employee_id,
            action="DELETE",
            actor=user,
            summary=f"Pegawai {employee_email} dihapus dari admin.",
            details={
                "email": employee_email,
                "assignments_deleted": deleted_assignments,
            },
        )
        flash("Pegawai berhasil dihapus.")
        return redirect(url_for("admin.employees"))

    @bp.route("/attendance", methods=["GET"])
    def attendance():
        user = _current_user()
        limit = ADMIN_LIST_LIMIT or 200
        sites = _list_sites()
        site_id_raw = (request.args.get("site_id") or "").strip()
        selected_site = None
        if site_id_raw.isdigit():
            target_id = int(site_id_raw)
            selected_site = next(
                (s for s in sites if int(s.get("id") or 0) == target_id),
                None,
            )
        client_scope = _client_admin_client_id(user)
        client_scope_emails = None
        if client_scope:
            today = _today_key()
            scoped_emails = {
                (a.get("employee_email") or "").lower()
                for a in _list_active_assignments(today)
                if int(a.get("client_id") or 0) == client_scope
            }
            client_scope_emails = scoped_emails
        records: list[dict] = []
        if selected_site:
            selected_site_id = int(selected_site.get("id") or 0)
            allowed_emails = {
                (emp.get("email") or "").strip().lower()
                for emp in _list_employees_by_site(selected_site_id)
                if emp.get("email")
            }
            if client_scope_emails is not None:
                allowed_emails = allowed_emails & client_scope_emails
            records = _attendance_live(limit=limit, allowed_emails=allowed_emails)
        return render_template(
            "dashboard/admin_attendance.html",
            user=user,
            records=records,
            sites=sites,
            selected_site=selected_site,
        )

    @bp.route("/manual_attendance", methods=["GET"])
    def manual_attendance_admin():
        user = _current_user()
        _require_hr_superadmin(user)
        status = (request.args.get("status") or "pending").lower()
        if status not in {"pending", "approved", "rejected"}:
            status = "pending"
        items = _fetch_manual_requests(status, user)
        return render_template(
            "dashboard/admin_manual_attendance.html",
            user=user,
            items=items,
            status=status,
            can_approve_manual=_can_approve_manual(user),
        )

    @bp.route("/manual_attendance/<int:request_id>/approve", methods=["POST"])
    def manual_attendance_approve(request_id: int):
        user = _current_user()
        _require_hr_superadmin(user)
        note = (request.form.get("note") or "").strip()
        request_row = _manual_request_by_id(request_id)
        if not request_row:
            flash("Data manual attendance tidak ditemukan.")
            return redirect(url_for("admin.manual_attendance_admin", status="pending"))
        if request_row.get("status") != "PENDING":
            flash("Manual attendance sudah diproses.")
            return redirect(url_for("admin.manual_attendance_admin", status="pending"))
        if not _approver_can_handle(user, request_row.get("employee_email") or ""):
            flash("Anda tidak memiliki akses untuk pegawai ini.")
            return redirect(url_for("admin.manual_attendance_admin", status="pending"))

        ok, message = _approve_manual_request_atomic(request_id, user, note or None)
        if not ok:
            flash(message)
            return redirect(url_for("admin.manual_attendance_admin", status="pending"))
        flash("Manual attendance disetujui.")
        return redirect(url_for("admin.manual_attendance_admin", status="pending"))

    @bp.route("/manual_attendance/<int:request_id>/reject", methods=["POST"])
    def manual_attendance_reject(request_id: int):
        user = _current_user()
        _require_hr_superadmin(user)
        note = (request.form.get("note") or "").strip()
        request_row = _manual_request_by_id(request_id)
        if not request_row:
            flash("Data manual attendance tidak ditemukan.")
            return redirect(url_for("admin.manual_attendance_admin", status="pending"))
        if request_row.get("status") != "PENDING":
            flash("Manual attendance sudah diproses.")
            return redirect(url_for("admin.manual_attendance_admin", status="pending"))
        if not _approver_can_handle(user, request_row.get("employee_email") or ""):
            flash("Anda tidak memiliki akses untuk pegawai ini.")
            return redirect(url_for("admin.manual_attendance_admin", status="pending"))
        if not note:
            flash("Alasan penolakan wajib diisi.")
            return redirect(url_for("admin.manual_attendance_admin", status="pending"))

        _reject_manual_request(request_id, user, note)
        flash("Manual attendance ditolak.")
        return redirect(url_for("admin.manual_attendance_admin", status="pending"))

    @bp.route("/approvals", methods=["GET"])
    def approvals():
        user = _current_user()
        manual_items = _fetch_manual_requests("pending", user)
        return render_template(
            "dashboard/admin_approvals.html",
            user=user,
            manual_items=manual_items,
            can_approve_manual=_can_approve_manual(user),
            can_approve_leave=_can_approve_leave(user),
        )

    @bp.route("/settings", methods=["GET"])
    def settings():
        user = _current_user()
        if not user:
            return abort(403)
        if user.role != "hr_superadmin":
            permissions = _get_role_permissions(user.role)
            if not (
                permissions.get("manage_settings_codes")
                or permissions.get("manage_settings_password")
            ):
                return abort(403)
        tab = (request.args.get("tab") or "users").lower()
        if tab not in {"users", "roles", "hr", "password"}:
            tab = "users"
        if user.role != "hr_superadmin":
            allowed_tabs = []
            if permissions.get("manage_settings_codes"):
                allowed_tabs.append("hr")
            if permissions.get("manage_settings_password"):
                allowed_tabs.append("password")
            if not allowed_tabs:
                return abort(403)
            if tab not in allowed_tabs:
                tab = allowed_tabs[0]
        users = [u for u in _list_users() if u.get("role") in ADMIN_ROLES]
        sites = _list_sites()
        clients = _clients()
        supervisor_sites = _get_supervisor_sites_map()
        registration_codes = _list_employee_registration_codes()
        role_permissions = {
            role: _get_role_permissions(role) for role in ADMIN_ROLE_OPTIONS
        }
        return render_template(
            "dashboard/admin_settings.html",
            user=user,
            tab=tab,
            users=users,
            sites=sites,
            clients=clients,
            supervisor_sites=supervisor_sites,
            registration_codes=registration_codes,
            role_options=ADMIN_ROLE_OPTIONS,
            role_permissions=role_permissions,
            permission_labels=ROLE_PERMISSION_LABELS,
            permission_keys=ROLE_PERMISSION_KEYS,
        )

    @bp.route("/settings/registration-codes/create", methods=["POST"])
    def settings_registration_codes_create():
        user = _current_user()
        _require_admin(user)
        count_raw = (request.form.get("registrant_count") or "").strip()
        try:
            registrant_count = int(count_raw)
        except ValueError:
            flash("Jumlah pendaftar wajib angka.")
            return redirect(url_for("admin.settings", tab="hr"))
        if registrant_count < 1 or registrant_count > 20:
            flash("Jumlah pendaftar harus 1 - 20.")
            return redirect(url_for("admin.settings", tab="hr"))
        code = _create_employee_registration_code(registrant_count)
        flash(f"Kode berhasil dibuat: {code}")
        return redirect(url_for("admin.settings", tab="hr"))

    @bp.route("/settings/users/create", methods=["POST"])
    def settings_users_create():
        user = _current_user()
        _require_hr_superadmin(user)
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        role = (request.form.get("role") or "admin_asistent").strip()
        password = (request.form.get("password") or "").strip()

        if not _looks_like_email(email):
            flash("Email tidak valid.")
            return redirect(url_for("admin.settings", tab="users"))
        if role not in ADMIN_ROLE_OPTIONS:
            flash("Role tidak valid.")
            return redirect(url_for("admin.settings", tab="users"))
        if role == "hr_superadmin" and _active_hr_superadmin_count():
            flash("HR Superadmin aktif sudah ada.")
            return redirect(url_for("admin.settings", tab="users"))
        if _get_user_by_email(email):
            flash("Email sudah terdaftar.")
            return redirect(url_for("admin.settings", tab="users"))
        if len(password) < 6:
            flash("Password awal minimal 6 karakter.")
            return redirect(url_for("admin.settings", tab="users"))
        _create_user(name=name, email=email, role=role, password=password)
        flash("User berhasil ditambahkan.")
        return redirect(url_for("admin.settings", tab="users"))

    @bp.route("/settings/users/<int:user_id>/update", methods=["POST"])
    def settings_users_update(user_id: int):
        user = _current_user()
        _require_hr_superadmin(user)
        target = _get_user_by_id(user_id)
        if not target:
            flash("User tidak ditemukan.")
            return redirect(url_for("admin.settings", tab="users"))
        if _row_get(target, "role") not in ADMIN_ROLES:
            flash("User bukan admin.")
            return redirect(url_for("admin.settings", tab="users"))
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        role = (request.form.get("role") or "admin_asistent").strip()
        is_active = 1 if request.form.get("is_active") == "1" else 0

        if not _looks_like_email(email):
            flash("Email tidak valid.")
            return redirect(url_for("admin.settings", tab="users"))
        if role not in ADMIN_ROLE_OPTIONS:
            flash("Role tidak valid.")
            return redirect(url_for("admin.settings", tab="users"))
        if user_id == user.id and role != "hr_superadmin":
            flash("HR Superadmin tidak boleh mengubah role sendiri.")
            return redirect(url_for("admin.settings", tab="users"))
        if role == "hr_superadmin" and _active_hr_superadmin_count(exclude_user_id=user_id):
            flash("HR Superadmin aktif sudah ada.")
            return redirect(url_for("admin.settings", tab="users"))
        if user_id == user.id and is_active == 0:
            flash("HR Superadmin tidak boleh dinonaktifkan.")
            return redirect(url_for("admin.settings", tab="users"))
        existing = _get_user_by_email(email)
        if existing and int(existing["id"]) != user_id:
            flash("Email sudah terdaftar.")
            return redirect(url_for("admin.settings", tab="users"))

        _update_user_basic(
            user_id=user_id,
            name=name,
            role=role,
            is_active=is_active,
            email=email,
        )
        flash("User berhasil diperbarui.")
        return redirect(url_for("admin.settings", tab="users"))

    @bp.route("/settings/users/<int:user_id>/toggle", methods=["POST"])
    def settings_users_toggle(user_id: int):
        user = _current_user()
        _require_hr_superadmin(user)
        target = _get_user_by_id(user_id)
        if not target:
            flash("User tidak ditemukan.")
            return redirect(url_for("admin.settings", tab="users"))
        if _row_get(target, "role") not in ADMIN_ROLES:
            flash("User bukan admin.")
            return redirect(url_for("admin.settings", tab="users"))
        if user_id == user.id:
            flash("HR Superadmin tidak boleh dinonaktifkan.")
            return redirect(url_for("admin.settings", tab="users"))
        is_active = 0 if int(target["is_active"] or 0) == 1 else 1
        if target["role"] == "hr_superadmin" and is_active == 1 and _active_hr_superadmin_count(exclude_user_id=user_id):
            flash("HR Superadmin aktif sudah ada.")
            return redirect(url_for("admin.settings", tab="users"))
        _update_user_basic(user_id=user_id, name=target["name"] or "", role=target["role"], is_active=is_active)
        flash("Status user diperbarui.")
        return redirect(url_for("admin.settings", tab="users"))

    @bp.route("/settings/users/<int:user_id>/reset_password", methods=["POST"])
    def settings_users_reset_password(user_id: int):
        user = _current_user()
        _require_hr_superadmin(user)
        target = _get_user_by_id(user_id)
        if not target:
            flash("User tidak ditemukan.")
            return redirect(url_for("admin.settings", tab="users"))
        if _row_get(target, "role") not in ADMIN_ROLES:
            flash("User bukan admin.")
            return redirect(url_for("admin.settings", tab="users"))
        hr_password = (request.form.get("hr_password") or "").strip()
        new_password = (request.form.get("new_password") or "").strip()
        new_password2 = (request.form.get("new_password2") or "").strip()
        row = _get_user_by_id(user.id)
        if not row or not check_password_hash(row["password_hash"], hr_password):
            flash("Konfirmasi password HR gagal.")
            return redirect(url_for("admin.settings", tab="users"))
        if len(new_password) < 6:
            flash("Password baru minimal 6 karakter.")
            return redirect(url_for("admin.settings", tab="users"))
        if new_password != new_password2:
            flash("Konfirmasi password baru tidak sama.")
            return redirect(url_for("admin.settings", tab="users"))
        _update_user_password(user_id, new_password, 1)
        flash("Password berhasil di-reset.")
        return redirect(url_for("admin.settings", tab="users"))

    @bp.route("/settings/users/<int:user_id>/delete", methods=["POST"])
    def settings_users_delete(user_id: int):
        user = _current_user()
        _require_hr_superadmin(user)
        target = _get_user_by_id(user_id)
        if not target:
            flash("User tidak ditemukan.")
            return redirect(url_for("admin.settings", tab="users"))
        if _row_get(target, "role") not in ADMIN_ROLES:
            flash("User bukan admin.")
            return redirect(url_for("admin.settings", tab="users"))
        if user_id == user.id:
            flash("HR Superadmin tidak boleh menghapus akun sendiri.")
            return redirect(url_for("admin.settings", tab="users"))
        if target["role"] == "hr_superadmin" and int(target["is_active"] or 0) == 1:
            if _active_hr_superadmin_count(exclude_user_id=user_id) == 0:
                flash("HR Superadmin terakhir tidak boleh dihapus.")
                return redirect(url_for("admin.settings", tab="users"))
        _delete_user(user_id)
        flash("User berhasil dihapus.")
        return redirect(url_for("admin.settings", tab="users"))

    @bp.route("/settings/users/<int:user_id>/assign_sites", methods=["POST"])
    def settings_users_assign_sites(user_id: int):
        user = _current_user()
        _require_hr_superadmin(user)
        target = _get_user_by_id(user_id)
        if not target:
            flash("User tidak ditemukan.")
            return redirect(url_for("admin.settings", tab="users"))
        if _row_get(target, "role") not in ADMIN_ROLES:
            flash("User bukan admin.")
            return redirect(url_for("admin.settings", tab="users"))
        if target["role"] != "supervisor":
            flash("Assign sites hanya untuk supervisor.")
            return redirect(url_for("admin.settings", tab="users"))
        site_ids = [int(sid) for sid in request.form.getlist("site_ids") if sid.isdigit()]
        _set_supervisor_sites(user_id, site_ids)
        flash("Site assignment diperbarui.")
        return redirect(url_for("admin.settings", tab="users"))

    @bp.route("/settings/roles/update", methods=["POST"])
    def settings_roles_update():
        user = _current_user()
        _require_hr_superadmin(user)
        role = (request.form.get("role") or "").strip()
        if role not in ADMIN_ROLE_OPTIONS:
            flash("Role tidak valid.")
            return redirect(url_for("admin.settings", tab="roles"))
        permissions: dict[str, bool] = {}
        for key in ROLE_PERMISSION_KEYS:
            permissions[key] = request.form.get(key) == "1"
        _set_role_permissions(role, permissions)
        flash("Role permissions diperbarui.")
        return redirect(url_for("admin.settings", tab="roles"))

    @bp.route("/settings/sites/create", methods=["POST"])
    def settings_sites_create():
        user = _current_user()
        _require_hr_or_client_admin(user)
        client_id_raw = (request.form.get("client_id") or "").strip()
        name = (request.form.get("name") or "").strip()
        timezone = (request.form.get("timezone") or "").strip()
        work_mode = (request.form.get("work_mode") or "").strip().upper()
        latitude_raw = (request.form.get("latitude") or "").strip()
        longitude_raw = (request.form.get("longitude") or "").strip()
        radius_raw = (request.form.get("radius_meters") or "").strip()
        notes = (request.form.get("notes") or "").strip()
        pic_name = (request.form.get("pic_name") or "").strip()
        pic_email = (request.form.get("pic_email") or "").strip().lower()
        if not client_id_raw:
            flash("Client wajib dipilih.")
            return redirect(url_for("admin.sites"))
        if not pic_email:
            flash("Email PIC wajib diisi.")
            return redirect(url_for("admin.sites", _anchor="add-site"))
        try:
            client_id = int(client_id_raw)
        except ValueError:
            flash("Client tidak valid.")
            return redirect(url_for("admin.sites"))
        if user and user.role == "client_admin":
            _require_client_admin_client(user, client_id)
        if not _get_client_by_id(client_id):
            flash("Client tidak ditemukan.")
            return redirect(url_for("admin.sites"))
        existing_pic = _get_user_by_email(pic_email)
        if existing_pic:
            if _row_get(existing_pic, "role") != "client_admin":
                flash("Email PIC sudah dipakai role lain.")
                return redirect(url_for("admin.sites"))
            existing_client = int(_row_get(existing_pic, "client_id") or 0)
            existing_site = int(_row_get(existing_pic, "site_id") or 0)
            if existing_client and existing_client != client_id:
                flash("Email PIC sudah terikat client lain.")
                return redirect(url_for("admin.sites"))
            if existing_site:
                flash("Email PIC sudah terikat site lain.")
                return redirect(url_for("admin.sites"))
        if not name:
            flash("Nama site wajib diisi.")
            return redirect(url_for("admin.sites"))
        try:
            latitude = float(latitude_raw)
            longitude = float(longitude_raw)
            radius_meters = int(radius_raw)
        except ValueError:
            flash("Latitude, longitude, dan radius wajib angka.")
            return redirect(url_for("admin.sites"))
        if radius_meters <= 0:
            flash("Radius harus lebih besar dari 0.")
            return redirect(url_for("admin.sites"))
        site_id = _create_site(
            client_id=client_id,
            name=name,
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
            notes=notes,
            timezone=timezone or None,
            work_mode=work_mode or None,
            pic_name=pic_name or None,
            pic_email=pic_email,
        )
        ok, message = _ensure_client_superadmin_user(pic_email, client_id, site_id)
        if not ok:
            flash(message)
            return redirect(url_for("admin.sites"))
        if message:
            if "dibuat" in message.lower():
                flash(f"{message} Password awal: {DEFAULT_CLIENT_PASSWORD} (segera ganti).")
            else:
                flash(message)
        flash("Site berhasil ditambahkan.")
        return redirect(url_for("admin.sites"))

    @bp.route("/settings/sites/<int:site_id>/update", methods=["POST"])
    def settings_sites_update(site_id: int):
        user = _current_user()
        _require_hr_or_client_admin(user)
        client_id_raw = (request.form.get("client_id") or "").strip()
        name = (request.form.get("name") or "").strip()
        timezone = (request.form.get("timezone") or "").strip()
        work_mode = (request.form.get("work_mode") or "").strip().upper()
        latitude_raw = (request.form.get("latitude") or "").strip()
        longitude_raw = (request.form.get("longitude") or "").strip()
        radius_raw = (request.form.get("radius_meters") or "").strip()
        notes = (request.form.get("notes") or "").strip()
        pic_name = (request.form.get("pic_name") or "").strip()
        pic_email = (request.form.get("pic_email") or "").strip().lower()
        if not client_id_raw:
            flash("Client wajib dipilih.")
            return redirect(url_for("admin.sites"))
        if not pic_email:
            flash("Email PIC wajib diisi.")
            return redirect(url_for("admin.sites"))
        try:
            client_id = int(client_id_raw)
        except ValueError:
            flash("Client tidak valid.")
            return redirect(url_for("admin.sites"))
        if user and user.role == "client_admin":
            _require_client_admin_client(user, client_id)
        if not _get_client_by_id(client_id):
            flash("Client tidak ditemukan.")
            return redirect(url_for("admin.sites"))
        existing_pic = _get_user_by_email(pic_email)
        if existing_pic:
            if _row_get(existing_pic, "role") != "client_admin":
                flash("Email PIC sudah dipakai role lain.")
                return redirect(url_for("admin.sites"))
            existing_client = int(_row_get(existing_pic, "client_id") or 0)
            existing_site = int(_row_get(existing_pic, "site_id") or 0)
            if existing_client and existing_client != client_id:
                flash("Email PIC sudah terikat client lain.")
                return redirect(url_for("admin.sites"))
            if existing_site and existing_site != site_id:
                flash("Email PIC sudah terikat site lain.")
                return redirect(url_for("admin.sites"))
        if not name:
            flash("Nama site wajib diisi.")
            return redirect(url_for("admin.sites"))
        try:
            latitude = float(latitude_raw)
            longitude = float(longitude_raw)
            radius_meters = int(radius_raw)
        except ValueError:
            flash("Latitude, longitude, dan radius wajib angka.")
            return redirect(url_for("admin.sites"))
        if radius_meters <= 0:
            flash("Radius harus lebih besar dari 0.")
            return redirect(url_for("admin.sites"))
        ok, message = _ensure_client_superadmin_user(pic_email, client_id, site_id)
        if not ok:
            flash(message)
            return redirect(url_for("admin.sites"))
        _update_site(
            site_id=site_id,
            client_id=client_id,
            name=name,
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
            notes=notes,
            timezone=timezone or None,
            work_mode=work_mode or None,
            pic_name=pic_name or None,
            pic_email=pic_email,
        )
        if message:
            if "dibuat" in message.lower():
                flash(f"{message} Password awal: {DEFAULT_CLIENT_PASSWORD} (segera ganti).")
            else:
                flash(message)
        flash("Site berhasil diperbarui.")
        return redirect(url_for("admin.sites"))

    @bp.route("/settings/sites/<int:site_id>/toggle", methods=["POST"])
    def settings_sites_toggle(site_id: int):
        user = _current_user()
        _require_hr_or_client_admin(user)
        current = next((s for s in _list_sites() if int(s["id"]) == site_id), None)
        if not current:
            flash("Site tidak ditemukan.")
            return redirect(url_for("admin.sites"))
        if user and user.role == "client_admin":
            _require_client_admin_site(user, site_id)
        is_active = 0 if int(current["is_active"] or 0) == 1 else 1
        _toggle_site(site_id, is_active)
        flash("Status site diperbarui.")
        return redirect(url_for("admin.sites"))

    @bp.route("/settings/sites/<int:site_id>/delete", methods=["POST"])
    def settings_sites_delete(site_id: int):
        user = _current_user()
        _require_hr_or_client_admin(user)
        current = next((s for s in _list_sites() if int(s["id"]) == site_id), None)
        if not current:
            flash("Site tidak ditemukan.")
            return redirect(url_for("admin.sites"))
        if user and user.role == "client_admin":
            _require_client_admin_site(user, site_id)
        try:
            _delete_site(site_id)
            flash("Site berhasil dihapus.")
        except sqlite3.IntegrityError:
            flash("Site tidak dapat dihapus karena masih memiliki data terkait.")
        return redirect(url_for("admin.sites"))

    @bp.route("/settings/shifts/create", methods=["POST"])
    def settings_shifts_create():
        user = _current_user()
        _require_hr_superadmin(user)
        name = (request.form.get("name") or "").strip()
        start_time = (request.form.get("start_time") or "").strip()
        end_time = (request.form.get("end_time") or "").strip()
        grace_minutes = int(request.form.get("grace_minutes") or 0)
        if not name:
            flash("Nama shift wajib diisi.")
            return redirect(url_for("admin.shifts"))
        _create_shift(name=name, start_time=start_time, end_time=end_time, grace_minutes=grace_minutes)
        flash("Shift berhasil ditambahkan.")
        return redirect(url_for("admin.shifts"))

    @bp.route("/settings/shifts/<int:shift_id>/update", methods=["POST"])
    def settings_shifts_update(shift_id: int):
        user = _current_user()
        _require_hr_superadmin(user)
        name = (request.form.get("name") or "").strip()
        start_time = (request.form.get("start_time") or "").strip()
        end_time = (request.form.get("end_time") or "").strip()
        grace_minutes = int(request.form.get("grace_minutes") or 0)
        if not name:
            flash("Nama shift wajib diisi.")
            return redirect(url_for("admin.shifts"))
        _update_shift(shift_id=shift_id, name=name, start_time=start_time, end_time=end_time, grace_minutes=grace_minutes)
        flash("Shift berhasil diperbarui.")
        return redirect(url_for("admin.shifts"))

    @bp.route("/settings/shifts/<int:shift_id>/toggle", methods=["POST"])
    def settings_shifts_toggle(shift_id: int):
        user = _current_user()
        _require_hr_superadmin(user)
        current = next((s for s in _list_shifts() if int(s["id"]) == shift_id), None)
        if not current:
            flash("Shift tidak ditemukan.")
            return redirect(url_for("admin.shifts"))
        is_active = 0 if int(current["is_active"] or 0) == 1 else 1
        _toggle_shift(shift_id, is_active)
        flash("Status shift diperbarui.")
        return redirect(url_for("admin.shifts"))

    @bp.route("/settings/shifts/<int:shift_id>/delete", methods=["POST"])
    def settings_shifts_delete(shift_id: int):
        user = _current_user()
        _require_hr_superadmin(user)
        current = next((s for s in _list_shifts() if int(s["id"]) == shift_id), None)
        if not current:
            flash("Shift tidak ditemukan.")
            return redirect(url_for("admin.shifts"))
        try:
            _delete_shift(shift_id)
            flash("Shift berhasil dihapus.")
        except sqlite3.IntegrityError:
            flash("Shift tidak dapat dihapus karena masih digunakan oleh data lain.")
        return redirect(url_for("admin.shifts"))

    return bp


def _clients():
    return _list_clients()


def _employees(query: str | None = None, limit: int | None = None, offset: int = 0):
    return _list_employees(query=query, limit=limit, offset=offset)


def _client_name_by_id(client_id: int | None) -> str | None:
    if not client_id:
        return None
    conn = _db_connect()
    try:
        row = conn.execute("SELECT name FROM clients WHERE id = ?", (client_id,)).fetchone()
        return row["name"] if row else None
    finally:
        conn.close()


def _attendance_live(
    limit: int = 200,
    offset: int = 0,
    employee_email: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    allowed_emails: set[str] | None = None,
) -> list[dict]:
    start = time.perf_counter()
    records: list[dict] = []
    if allowed_emails is not None and not allowed_emails:
        return []
    conn = _db_connect()
    try:
        if _table_exists(conn, "attendance"):
            base_query = """
                SELECT employee_name, employee_email, date, time, action, method, source, created_at
                FROM attendance
            """
            clauses = []
            params: list = []
            if employee_email:
                clauses.append("lower(employee_email) LIKE ?")
                params.append(f"%{employee_email.strip().lower()}%")
            if allowed_emails is not None:
                normalized = {e.lower() for e in allowed_emails if e}
                if not normalized:
                    return []
                placeholders = ",".join("?" for _ in normalized)
                clauses.append(f"lower(employee_email) IN ({placeholders})")
                params.extend(sorted(normalized))
            if date_from:
                clauses.append("COALESCE(date, substr(created_at, 1, 10)) >= ?")
                params.append(date_from)
            if date_to:
                clauses.append("COALESCE(date, substr(created_at, 1, 10)) <= ?")
                params.append(date_to)
            if clauses:
                base_query += " WHERE " + " AND ".join(clauses)
            base_query += " ORDER BY created_at DESC"
            base_query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            cur = conn.execute(base_query, tuple(params))
            for row in cur.fetchall():
                created_at = row["created_at"] or ""
                date = row["date"] or (created_at.split(" ")[0] if " " in created_at else "-")
                time_value = row["time"] or (
                    created_at.split(" ")[1] if " " in created_at else "-"
                )
                name = row["employee_name"] or row["employee_email"] or "-"
                raw_source = row["source"] or "sqlite"
                source_label = "-" if raw_source == "manual_request" else "sqlite"
                method = row["method"] or ("manual" if raw_source == "manual_request" else "-")
                records.append(
                    {
                        "employee": name,
                        "email": row["employee_email"] or "-",
                        "date": date,
                        "time": time_value,
                        "action": row["action"] or "-",
                        "method": method,
                        "source": source_label,
                        "created_at": created_at,
                    }
                )
    finally:
        conn.close()

    aggregated_records = _aggregate_attendance_records(records)
    aggregated_records = sorted(aggregated_records, key=lambda row: row.get("created_at", ""), reverse=True)
    aggregated_records = aggregated_records[:limit]
    _perf_log("attendance_live", start, f"rows={len(aggregated_records)} limit={limit}")
    return aggregated_records


def _aggregate_attendance_records(rows: list[dict]) -> list[dict]:
    aggregated: list[dict] = []
    seen: dict[str, dict] = {}
    for row in rows:
        email_key = (row.get("email") or "").strip().lower()
        date_value = row.get("date") or "-"
        key = f"{email_key}|{date_value}"
        entry = seen.get(key)
        if not entry:
            entry = {
                "employee": row.get("employee") or "-",
                "email": row.get("email") or "-",
                "date": row.get("date") or "-",
                "check_in": "-",
                "check_out": "-",
                "method": row.get("method") or "-",
                "source": row.get("source") or "-",
                "created_at": row.get("created_at") or "",
            }
            aggregated.append(entry)
            seen[key] = entry
        action_lower = (row.get("action") or "").lower()
        time_value = row.get("time") or "-"
        if "out" in action_lower:
            if time_value and time_value != "-":
                entry["check_out"] = time_value
        else:
            if time_value and time_value != "-":
                entry["check_in"] = time_value
        if row.get("method"):
            entry["method"] = row["method"]
        created_at = row.get("created_at")
        if created_at:
            if not entry.get("created_at"):
                entry["created_at"] = created_at
            elif created_at > entry["created_at"]:
                entry["created_at"] = created_at
    return aggregated


def _chunk_items(items: list[str], size: int) -> list[list[str]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def _attendance_rows_for_emails(
    allowed_emails: set[str],
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    start = time.perf_counter()
    normalized_emails = sorted(
        {email.strip().lower() for email in allowed_emails if email and email.strip()}
    )
    if not normalized_emails:
        return []
    chunk_size = 300
    conn = _db_connect()
    try:
        records: list[dict] = []
        base_query = """
            SELECT employee_name, employee_email, date, time, action, method, source, created_at
            FROM attendance
        """
        date_clauses: list[str] = []
        date_params: list[str] = []
        if date_from:
            date_clauses.append("COALESCE(date, substr(created_at, 1, 10)) >= ?")
            date_params.append(date_from)
        if date_to:
            date_clauses.append("COALESCE(date, substr(created_at, 1, 10)) <= ?")
            date_params.append(date_to)
        for chunk in _chunk_items(normalized_emails, chunk_size):
            clauses = date_clauses.copy()
            params = list(date_params)
            placeholders = ",".join("?" for _ in chunk)
            clauses.insert(0, f"lower(employee_email) IN ({placeholders})")
            params = list(chunk) + params
            query = base_query
            if clauses:
                query += " WHERE " + " AND ".join(clauses)
            query += " ORDER BY created_at DESC"
            cur = conn.execute(query, tuple(params))
            for row in cur.fetchall():
                created_at = row["created_at"] or ""
                date_value = row["date"] or (created_at.split(" ")[0] if " " in created_at else "-")
                time_value = row["time"] or (created_at.split(" ")[1] if " " in created_at else "-")
                name = row["employee_name"] or row["employee_email"] or "-"
                raw_source = row["source"] or "sqlite"
                source_label = "-" if raw_source == "manual_request" else "sqlite"
                method = row["method"] or ("manual" if raw_source == "manual_request" else "-")
                records.append(
                    {
                        "employee": name,
                        "email": row["employee_email"] or "-",
                        "date": date_value,
                        "time": time_value,
                        "action": row["action"] or "-",
                        "method": method,
                        "source": source_label,
                        "created_at": created_at,
                    }
                )
        records = sorted(records, key=lambda row: row.get("created_at", ""), reverse=True)
        _perf_log("attendance_csv_rows", start, f"rows={len(records)}")
        return records
    finally:
        conn.close()


def _leave_status_by_email_for_date(today: str, emails: set[str]) -> dict[str, dict]:
    if not emails:
        return {}
    conn = _db_connect()
    try:
        if not _table_exists(conn, "leave_requests"):
            return {}
        placeholders = ",".join("?" for _ in emails)
        params = [*sorted({e.lower() for e in emails if e}), today, today]
        cur = conn.execute(
            f"""
            SELECT lower(employee_email) AS email, lower(leave_type) AS leave_type, status, updated_at, created_at
            FROM leave_requests
            WHERE lower(employee_email) IN ({placeholders})
              AND status != 'rejected'
              AND date_from <= ?
              AND date_to >= ?
            ORDER BY updated_at DESC, created_at DESC
            """,
            params,
        )
        status_by_email: dict[str, dict] = {}
        for row in cur.fetchall():
            email = (row["email"] or "").lower()
            if not email:
                continue
            status = (row["status"] or "").lower()
            leave_type = (row["leave_type"] or "").lower()
            current = status_by_email.get(email)
            if current and current.get("status") == "pending":
                continue
            if status == "pending":
                status_by_email[email] = {"status": "pending", "type": leave_type}
                continue
            if status == "approved" and not current:
                status_by_email[email] = {"status": "approved", "type": leave_type}
        return status_by_email
    finally:
        conn.close()


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5020, debug=False)
else:
    # For WSGI/ASGI servers
    app = create_app()
