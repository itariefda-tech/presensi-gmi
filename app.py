from __future__ import annotations

import re
import os
import math
import sqlite3
from datetime import datetime
from dataclasses import dataclass
from typing import Dict

from flask import Flask, jsonify, render_template, request, session, Blueprint, abort, redirect, url_for, flash
from werkzeug.utils import secure_filename


@dataclass
class AuthResult:
    ok: bool
    message: str
    next_url: str | None = None


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret-change-me")

    app.register_blueprint(admin_bp())
    _init_db()

    @app.route("/api/auth/login", methods=["POST"])
    def login():
        data = _get_json()
        result = _validate_login(data)
        status = 200 if result.ok else 400
        return jsonify(result.__dict__), status

    @app.route("/api/auth/signup", methods=["POST"])
    def signup():
        data = request.form or {}
        invite = (data.get("invite_code") or "").strip()
        email = (data.get("email") or "").strip()
        p1 = data.get("password", "")
        p2 = data.get("password2", "")
        selfie_file = request.files.get("selfie")

        if not invite:
            return jsonify(ok=False, message="Kode undangan wajib."), 400
        if not _looks_like_email(email):
            return jsonify(ok=False, message="Email tidak valid."), 400
        if len(p1) < 6:
            return jsonify(ok=False, message="Password minimal 6 karakter."), 400
        if p1 != p2:
            return jsonify(ok=False, message="Password tidak sama."), 400
        if not selfie_file or not selfie_file.filename:
            return jsonify(ok=False, message="Selfie wajib untuk daftar."), 400

        # Demo: pretend to accept any code with prefix GMI-
        if not invite.upper().startswith("GMI-"):
            return jsonify(ok=False, message="Kode undangan tidak dikenal (demo)."), 400

        try:
            selfie_path = _save_upload(selfie_file, "uploads/selfies", 2 * 1024 * 1024)
        except ValueError as err:
            return jsonify(ok=False, message=str(err)), 400

        DEMO_USERS[email.lower()] = {"selfie_path": selfie_path}
        return jsonify(ok=True, message="Signup (demo). Backend siap validasi kode undangan."), 200

    @app.route("/api/auth/forgot", methods=["POST"])
    def forgot():
        data = _get_json()
        email = data.get("email", "").strip()
        method = data.get("method", "whatsapp_otp")

        if not _looks_like_email(email):
            return jsonify(ok=False, message="Email wajib diisi."), 400

        route = "WhatsApp OTP" if method == "whatsapp_otp" else "Email"
        return jsonify(ok=True, message=f"Reset (demo) via {route}."), 200

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify(status="ok"), 200

    @app.route("/", methods=["GET"])
    def index():
        return render_template("index.html", theme="dark")

    @app.route("/dashboard/pegawai", methods=["GET"])
    def dashboard_employee():
        user = _current_user()
        if not user or user.role != "employee":
            return abort(403)
        return render_template("dashboard/employee.html", user=user)

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

    @app.route("/logout", methods=["GET"])
    def logout():
        session.clear()
        return redirect("/")

    @app.route("/api/attendance/checkin", methods=["POST"])
    def attendance_checkin():
        user = _current_user()
        if not user or user.role != "employee":
            return _json_forbidden()
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
        if not lat or not lng:
            return jsonify(ok=False, message="Lokasi GPS wajib diisi."), 400
        try:
            lat_f = float(lat)
            lng_f = float(lng)
        except ValueError:
            return jsonify(ok=False, message="Lokasi GPS tidak valid."), 400
        if not _within_radius(lat_f, lng_f):
            return jsonify(ok=False, message="Lokasi di luar radius 100m."), 400
        if method == "gps_selfie" and (not selfie_file or not selfie_file.filename):
            return jsonify(ok=False, message="Selfie wajib untuk presensi."), 400
        if method == "qr":
            ok, msg = _validate_qr_data(qr_data)
            if not ok:
                return jsonify(ok=False, message=msg), 400
        selfie_path = None
        if selfie_file and selfie_file.filename:
            try:
                selfie_path = _save_upload(selfie_file, "uploads/attendance", 2 * 1024 * 1024)
            except ValueError as err:
                return jsonify(ok=False, message=str(err)), 400

        record = {
            "id": _next_id(DEMO_ATTENDANCE),
            "employee_email": user.email,
            "action": "checkin",
            "method": "gps+selfie" if method == "gps_selfie" else method,
            "lat": lat_f,
            "lng": lng_f,
            "accuracy": accuracy,
            "device_time": device_time,
            "selfie_path": selfie_path,
            "qr_data": qr_data if method == "qr" else None,
            "status": "submitted",
            "created_at": _now_ts(),
            "approver": None,
            "approved_at": None,
            "note": None,
        }
        DEMO_ATTENDANCE.append(record)
        return jsonify(ok=True, message="Presensi tercatat (demo).", data=record), 200

    @app.route("/api/attendance/checkout", methods=["POST"])
    def attendance_checkout():
        user = _current_user()
        if not user or user.role != "employee":
            return _json_forbidden()
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
        if not lat or not lng:
            return jsonify(ok=False, message="Lokasi GPS wajib diisi."), 400
        try:
            lat_f = float(lat)
            lng_f = float(lng)
        except ValueError:
            return jsonify(ok=False, message="Lokasi GPS tidak valid."), 400
        if not _within_radius(lat_f, lng_f):
            return jsonify(ok=False, message="Lokasi di luar radius 100m."), 400
        if method == "gps_selfie" and (not selfie_file or not selfie_file.filename):
            return jsonify(ok=False, message="Selfie wajib untuk presensi."), 400
        if method == "qr":
            ok, msg = _validate_qr_data(qr_data)
            if not ok:
                return jsonify(ok=False, message=msg), 400
        selfie_path = None
        if selfie_file and selfie_file.filename:
            try:
                selfie_path = _save_upload(selfie_file, "uploads/attendance", 2 * 1024 * 1024)
            except ValueError as err:
                return jsonify(ok=False, message=str(err)), 400

        record = {
            "id": _next_id(DEMO_ATTENDANCE),
            "employee_email": user.email,
            "action": "checkout",
            "method": "gps+selfie" if method == "gps_selfie" else method,
            "lat": lat_f,
            "lng": lng_f,
            "accuracy": accuracy,
            "device_time": device_time,
            "selfie_path": selfie_path,
            "qr_data": qr_data if method == "qr" else None,
            "status": "submitted",
            "created_at": _now_ts(),
            "approver": None,
            "approved_at": None,
            "note": None,
        }
        DEMO_ATTENDANCE.append(record)
        return jsonify(ok=True, message="Check-out tercatat (demo).", data=record), 200

    @app.route("/api/attendance/today", methods=["GET"])
    def attendance_today():
        user = _current_user()
        if not user or user.role != "employee":
            return _json_forbidden()
        today = _today_key()
        records = [
            r for r in DEMO_ATTENDANCE
            if r.get("employee_email") == user.email and r.get("created_at", "").startswith(today)
        ]
        records = sorted(records, key=lambda r: r.get("created_at", ""), reverse=True)
        return jsonify(ok=True, data=records[:10]), 200

    @app.route("/api/attendance/manual", methods=["POST"])
    def attendance_manual():
        user = _current_user()
        if not user or user.role not in {"supervisor", "koordinator"}:
            return _json_forbidden()
        data = _get_json()
        employee_email = (data.get("employee_email") or "").strip()
        reason = (data.get("reason") or "").strip()
        lat = data.get("lat")
        lon = data.get("lon")

        if not _looks_like_email(employee_email):
            return jsonify(ok=False, message="Email pegawai wajib diisi."), 400
        if not reason:
            return jsonify(ok=False, message="Alasan wajib diisi."), 400

        record = {
            "id": _next_id(DEMO_ATTENDANCE),
            "employee_email": employee_email,
            "method": "manual",
            "lat": lat,
            "lon": lon,
            "selfie": None,
            "qr_data": None,
            "status": "pending",
            "created_at": _now_ts(),
            "created_by": user.email,
            "approver": None,
            "approved_at": None,
            "note": reason,
        }
        DEMO_ATTENDANCE.append(record)
        return jsonify(ok=True, message="Manual attendance dikirim (pending).", data=record), 200

    @app.route("/api/attendance/pending", methods=["GET"])
    def attendance_pending():
        user = _current_user()
        if not user or user.role not in ADMIN_ROLES:
            return _json_forbidden()
        pending = [r for r in DEMO_ATTENDANCE if r.get("method") == "manual" and r.get("status") == "pending"]
        return jsonify(ok=True, data=pending), 200

    @app.route("/api/attendance/approve", methods=["POST"])
    def attendance_approve():
        user = _current_user()
        if not user or user.role not in {"supervisor", "koordinator"}:
            return _json_forbidden()
        data = _get_json()
        rid = data.get("id")
        note = (data.get("note") or "").strip()
        record = _find_by_id(DEMO_ATTENDANCE, rid)
        if not record or record.get("method") != "manual":
            return jsonify(ok=False, message="Data attendance tidak ditemukan."), 404
        if record.get("status") != "pending":
            return jsonify(ok=False, message="Attendance sudah diproses."), 400

        record["status"] = "approved"
        record["approver"] = user.email
        record["approved_at"] = _now_ts()
        record["note"] = note or record.get("note")
        return jsonify(ok=True, message="Attendance disetujui."), 200

    @app.route("/api/leave/request", methods=["POST"])
    def leave_request():
        user = _current_user()
        if not user or user.role != "employee":
            return _json_forbidden()
        data = _get_json()
        leave_type = (data.get("type") or "").strip()
        date_from = (data.get("date_from") or "").strip()
        date_to = (data.get("date_to") or "").strip()
        reason = (data.get("reason") or "").strip()
        attachment = data.get("attachment")
        attachment_base64 = data.get("attachment_base64")

        if leave_type not in {"izin", "sakit", "absen"}:
            return jsonify(ok=False, message="Tipe izin tidak valid."), 400
        if not date_from or not date_to:
            return jsonify(ok=False, message="Tanggal izin wajib diisi."), 400
        if not reason:
            return jsonify(ok=False, message="Alasan wajib diisi."), 400

        record = {
            "id": _next_id(DEMO_LEAVE_REQUESTS),
            "employee_email": user.email,
            "type": leave_type,
            "date_from": date_from,
            "date_to": date_to,
            "reason": reason,
            "attachment": attachment,
            "attachment_base64": attachment_base64,
            "status": "pending",
            "created_at": _now_ts(),
            "approver": None,
            "approved_at": None,
            "note": None,
        }
        DEMO_LEAVE_REQUESTS.append(record)
        return jsonify(ok=True, message="Pengajuan izin dikirim.", data=record), 200

    @app.route("/api/leave/my", methods=["GET"])
    def leave_my():
        user = _current_user()
        if not user or user.role != "employee":
            return _json_forbidden()
        mine = [r for r in DEMO_LEAVE_REQUESTS if r.get("employee_email") == user.email]
        mine = sorted(mine, key=lambda r: r.get("created_at", ""), reverse=True)
        return jsonify(ok=True, data=mine), 200

    @app.route("/api/leave/pending", methods=["GET"])
    def leave_pending():
        user = _current_user()
        if not user or user.role not in ADMIN_ROLES:
            return _json_forbidden()
        pending = [r for r in DEMO_LEAVE_REQUESTS if r.get("status") == "pending"]
        pending = sorted(pending, key=lambda r: r.get("created_at", ""), reverse=True)
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
        record = _find_by_id(DEMO_LEAVE_REQUESTS, rid)
        if not record:
            return jsonify(ok=False, message="Pengajuan tidak ditemukan."), 404
        if record.get("status") != "pending":
            return jsonify(ok=False, message="Pengajuan sudah diproses."), 400
        if action == "reject" and not note:
            return jsonify(ok=False, message="Alasan penolakan wajib diisi."), 400

        record["status"] = "rejected" if action == "reject" else "approved"
        record["approver"] = user.email
        record["approved_at"] = _now_ts()
        record["note"] = note or record.get("note")
        message = "Pengajuan ditolak." if action == "reject" else "Pengajuan disetujui."
        return jsonify(ok=True, message=message), 200

    return app


def _looks_like_email(value: str) -> bool:
    if not value:
        return False
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value))


def _validate_login(data: Dict[str, str]) -> AuthResult:
    email = data.get("email", "").strip()
    password = data.get("password", "")
    theme = data.get("theme", "dark")

    if not _looks_like_email(email):
        return AuthResult(False, "Isi email dengan benar.")
    if not password:
        return AuthResult(False, "Isi password dulu.")

    entry = DEMO_ADMINS.get(email.lower())
    if entry:
        if password != entry["password"]:
            return AuthResult(False, "Password salah.")
        role = entry["role"]
        selfie_path = None
    else:
        role = _role_from_email(email)
        selfie_path = (DEMO_USERS.get(email.lower()) or {}).get("selfie_path")
    user = User(email=email, role=role, theme=theme, selfie_path=selfie_path)
    _persist_user(user)

    target = "/dashboard/admin" if role in ADMIN_ROLES else "/dashboard/pegawai"
    return AuthResult(True, f"Login (demo). Tema {theme}.", target)


def _get_json() -> Dict[str, str]:
    if request.is_json:
        return request.get_json(force=True) or {}
    return request.form.to_dict() if request.form else {}


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("PRESENSI_DB_PATH") or os.path.join(BASE_DIR, "presensi.db")


# =========================
# Demo data & helpers
# =========================
ADMIN_ROLES = {"admin", "client_admin", "supervisor", "koordinator"}
DEMO_ADMINS = {
    "hr@gmi.com": {"password": "hr123456", "role": "admin"},
}
DEMO_USERS = {}
DEMO_ATTENDANCE = []
DEMO_LEAVE_REQUESTS = []
DEMO_GPS_CENTER = (-6.5706, 107.7603)
DEMO_GPS_RADIUS_METERS = 100
DEMO_QR_PREFIX = "GMI-"
ADMIN_APPROVER_ROLES = {"admin", "client_admin"}


@dataclass
class User:
    email: str
    role: str
    theme: str = "dark"
    selfie_path: str | None = None


def _role_from_email(email: str) -> str:
    e = email.lower()
    if "client" in e:
        return "client_admin"
    if "supervisor" in e:
        return "supervisor"
    if "koordinator" in e or "koor" in e:
        return "koordinator"
    if "admin" in e:
        return "admin"
    return "employee"


def _persist_user(user: User) -> None:
    session["user"] = {
        "email": user.email,
        "role": user.role,
        "theme": user.theme,
        "selfie_path": user.selfie_path,
    }


def _current_user() -> User | None:
    data = session.get("user") or {}
    if not data:
        return None
    return User(
        email=data.get("email", ""),
        role=data.get("role", "employee"),
        theme=data.get("theme", "dark"),
        selfie_path=data.get("selfie_path"),
    )


def _require_admin(user: User | None) -> None:
    if not user or user.role not in ADMIN_ROLES:
        abort(403)


def _require_admin_approver(user: User | None) -> None:
    if not user or user.role not in ADMIN_APPROVER_ROLES:
        abort(403)


def _json_forbidden():
    return jsonify(ok=False, message="Unauthorized."), 403


def _next_id(records) -> int:
    if not records:
        return 1
    return max(int(r.get("id", 0)) for r in records) + 1


def _find_by_id(records, rid):
    try:
        rid = int(rid)
    except (TypeError, ValueError):
        return None
    for r in records:
        if int(r.get("id", 0)) == rid:
            return r
    return None


def _now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _today_key() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _save_upload(file_obj, subdir: str, max_size: int) -> str:
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
        raise ValueError("Ukuran file maksimal 2MB.")

    safe_name = secure_filename(file_obj.filename) or "upload.jpg"
    ts = datetime.now().strftime("%Y%m%d%H%M%S%f")
    filename = f"{ts}_{safe_name}"
    base_dir = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.join(base_dir, "static", subdir)
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, filename)
    file_obj.save(file_path)
    return f"{subdir}/{filename}"


def _db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    )
    return cur.fetchone() is not None


def _table_columns(conn: sqlite3.Connection, name: str) -> set[str]:
    cur = conn.execute(f"PRAGMA table_info({name})")
    return {row[1] for row in cur.fetchall()}


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = _table_columns(conn, table)
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {definition}")


def _init_db() -> None:
    conn = _db_connect()
    try:
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
                created_by_user_id TEXT NOT NULL,
                created_by_role TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING',
                reviewed_by_user_id TEXT,
                reviewed_at TEXT,
                review_note TEXT
            )
            """
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
                    source TEXT,
                    manual_request_id INTEGER,
                    created_at TEXT NOT NULL
                )
                """
            )
        else:
            _ensure_column(conn, "attendance", "source", "source TEXT")
            _ensure_column(conn, "attendance", "manual_request_id", "manual_request_id INTEGER")
    finally:
        conn.commit()
        conn.close()


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
    for entry in DEMO_ADMINS.values():
        if entry.get("role") == "supervisor":
            return True
    for email in DEMO_USERS.keys():
        if _role_from_email(email) == "supervisor":
            return True
    return False


def _can_submit_manual(user: User) -> bool:
    if user.role == "supervisor":
        return True
    if user.role == "koordinator":
        return not _has_supervisor_account()
    return False


def _can_approve_leave(user: User) -> bool:
    if user.role in ADMIN_APPROVER_ROLES:
        return True
    if user.role == "supervisor":
        return True
    if user.role == "koordinator":
        return not _has_supervisor_account()
    return False


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
                created_by_user_id, created_by_role, created_at, status
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


def _fetch_manual_requests(status: str) -> list[dict]:
    conn = _db_connect()
    try:
        status_key = status.upper()
        cur = conn.execute(
            """
            SELECT *
            FROM manual_attendance_requests
            WHERE status = ?
            ORDER BY
                CASE created_by_role
                    WHEN 'supervisor' THEN 1
                    WHEN 'koordinator' THEN 2
                    ELSE 3
                END,
                created_at DESC
            """,
            (status_key,),
        )
        return [dict(row) for row in cur.fetchall()]
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
                date, time, action, method, source, manual_request_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                request_row.get("employee_id"),
                request_row.get("employee_name"),
                request_row.get("employee_email"),
                request_row.get("date"),
                request_row.get("time"),
                request_row.get("action"),
                "manual",
                "manual_request",
                request_row.get("id"),
                _now_ts(),
            ),
        )
    finally:
        conn.commit()
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


def _validate_qr_data(qr_data: str) -> tuple[bool, str]:
    payload = (qr_data or "").strip()
    if not payload:
        return False, "QR code wajib di-scan."
    if len(payload) < 6 or len(payload) > 120:
        return False, "QR tidak valid (demo)."
    if not payload.upper().startswith(DEMO_QR_PREFIX):
        return False, "QR tidak dikenali (demo)."
    return True, "ok"


def admin_bp() -> Blueprint:
    bp = Blueprint("admin", __name__, url_prefix="/dashboard/admin")

    @bp.before_request
    def _guard():
        user = _current_user()
        _require_admin(user)

    @bp.route("/", methods=["GET"])
    def overview():
        user = _current_user()
        stats = {
            "clients": len(_clients()),
            "employees": len(_employees()),
            "attendance_today": len([a for a in _attendance() if a["status"] == "hadir"]),
        }
        return render_template("dashboard/admin_overview.html", user=user, stats=stats)

    @bp.route("/clients", methods=["GET"])
    def clients():
        user = _current_user()
        return render_template("dashboard/admin_clients.html", user=user, clients=_clients())

    @bp.route("/employees", methods=["GET"])
    def employees():
        user = _current_user()
        return render_template("dashboard/admin_employees.html", user=user, employees=_employees())

    @bp.route("/attendance", methods=["GET"])
    def attendance():
        user = _current_user()
        return render_template("dashboard/admin_attendance.html", user=user, records=_attendance())

    @bp.route("/manual_attendance", methods=["GET"])
    def manual_attendance_admin():
        user = _current_user()
        status = (request.args.get("status") or "pending").lower()
        if status not in {"pending", "approved", "rejected"}:
            status = "pending"
        items = _fetch_manual_requests(status)
        return render_template(
            "dashboard/admin_manual_attendance.html",
            user=user,
            items=items,
            status=status,
        )

    @bp.route("/manual_attendance/<int:request_id>/approve", methods=["POST"])
    def manual_attendance_approve(request_id: int):
        user = _current_user()
        _require_admin_approver(user)
        note = (request.form.get("note") or "").strip()
        request_row = _manual_request_by_id(request_id)
        if not request_row:
            flash("Data manual attendance tidak ditemukan.")
            return redirect(url_for("admin.manual_attendance_admin", status="pending"))
        if request_row.get("status") != "PENDING":
            flash("Manual attendance sudah diproses.")
            return redirect(url_for("admin.manual_attendance_admin", status="pending"))

        _approve_manual_request(request_id, user, note or None)
        _insert_manual_attendance_record(request_row)
        flash("Manual attendance disetujui.")
        return redirect(url_for("admin.manual_attendance_admin", status="pending"))

    @bp.route("/manual_attendance/<int:request_id>/reject", methods=["POST"])
    def manual_attendance_reject(request_id: int):
        user = _current_user()
        _require_admin_approver(user)
        note = (request.form.get("note") or "").strip()
        request_row = _manual_request_by_id(request_id)
        if not request_row:
            flash("Data manual attendance tidak ditemukan.")
            return redirect(url_for("admin.manual_attendance_admin", status="pending"))
        if request_row.get("status") != "PENDING":
            flash("Manual attendance sudah diproses.")
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
        manual_items = _fetch_manual_requests("pending")
        return render_template("dashboard/admin_approvals.html", user=user, manual_items=manual_items)

    return bp


def _clients():
    return [
        {"id": 1, "name": "PT Sinar Berkah", "sector": "Manufaktur", "since": "2021"},
        {"id": 2, "name": "RS Sehat Sentosa", "sector": "Kesehatan", "since": "2022"},
        {"id": 3, "name": "Mall Harmoni", "sector": "Retail", "since": "2019"},
    ]


def _employees():
    return [
        {"id": 101, "name": "Budi", "role": "Satpam", "client": "Mall Harmoni", "email": "budi@gmi.com"},
        {"id": 102, "name": "Sari", "role": "Cleaning Service", "client": "RS Sehat Sentosa", "email": "sari@gmi.com"},
        {"id": 103, "name": "Andi", "role": "Operator", "client": "PT Sinar Berkah", "email": "andi@gmi.com"},
        {"id": 104, "name": "Rina", "role": "Supir", "client": "PT Sinar Berkah", "email": "rina@gmi.com"},
    ]


def _attendance():
    return [
        {"id": 1, "name": "Budi", "client": "Mall Harmoni", "status": "hadir", "time": "07:58", "method": "gps+selfie"},
        {"id": 2, "name": "Sari", "client": "RS Sehat Sentosa", "status": "hadir", "time": "08:05", "method": "gps+selfie"},
        {"id": 3, "name": "Andi", "client": "PT Sinar Berkah", "status": "telat", "time": "08:20", "method": "gps"},
        {"id": 4, "name": "Rina", "client": "PT Sinar Berkah", "status": "izin", "time": "-", "method": "-"},
    ]


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5020, debug=False)
else:
    # For WSGI/ASGI servers
    app = create_app()
