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
from werkzeug.security import generate_password_hash, check_password_hash


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

        if _get_user_by_email(email):
            return jsonify(ok=False, message="Email sudah terdaftar."), 400

        _create_user(
            name=email.split("@")[0],
            email=email,
            role="employee",
            password=p1,
            selfie_path=selfie_path,
        )
        return jsonify(ok=True, message="Signup berhasil (demo)."), 200

    @app.route("/api/auth/forgot", methods=["POST"])
    def forgot():
        data = _get_json()
        email = data.get("email", "").strip()
        method = data.get("method", "whatsapp_otp")

        if not _looks_like_email(email):
            return jsonify(ok=False, message="Email wajib diisi."), 400

        route = "WhatsApp OTP" if method == "whatsapp_otp" else "Email"
        return jsonify(ok=True, message=f"Reset (demo) via {route}."), 200

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
        return jsonify(ok=True, message="Password berhasil diperbarui."), 200

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
        forbidden = _require_api_role(user, EMPLOYEE_ROLES)
        if forbidden:
            return forbidden
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
        forbidden = _require_api_role(user, EMPLOYEE_ROLES)
        if forbidden:
            return forbidden
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
        forbidden = _require_api_role(user, EMPLOYEE_ROLES)
        if forbidden:
            return forbidden
        today = _today_key()
        records = [
            r for r in DEMO_ATTENDANCE
            if r.get("employee_email") == user.email and r.get("created_at", "").startswith(today)
        ]
        records = sorted(records, key=lambda r: r.get("created_at", ""), reverse=True)
        return jsonify(ok=True, data=records[:10]), 200

    @app.route("/api/attendance/manual", methods=["POST"])
    def attendance_manual():
        # LEGACY / DEMO ONLY: Use /dashboard/manual_attendance + admin approvals (SQLite).
        user = _current_user()
        forbidden = _require_api_role(user, {"supervisor", "manager_operational"})
        if forbidden:
            return forbidden
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
        return jsonify(
            ok=True,
            message="Endpoint legacy (demo). Gunakan flow /dashboard/manual_attendance + approvals admin.",
            data=record,
        ), 200

    @app.route("/api/attendance/pending", methods=["GET"])
    def attendance_pending():
        # LEGACY / DEMO ONLY: Use SQLite manual_attendance_requests for pending list.
        user = _current_user()
        forbidden = _require_api_role(user, ADMIN_ROLES)
        if forbidden:
            return forbidden
        pending = [r for r in DEMO_ATTENDANCE if r.get("method") == "manual" and r.get("status") == "pending"]
        return jsonify(
            ok=True,
            message="Endpoint legacy (demo). Gunakan approvals admin (SQLite).",
            data=pending,
        ), 200

    @app.route("/api/attendance/approve", methods=["POST"])
    def attendance_approve():
        # LEGACY / DEMO ONLY: Manual attendance approvals handled via SQLite admin routes.
        user = _current_user()
        forbidden = _require_api_role(user, {"supervisor", "manager_operational"})
        if forbidden:
            return forbidden
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
        return jsonify(
            ok=True,
            message="Endpoint legacy (demo). Gunakan approvals admin (SQLite).",
        ), 200

    @app.route("/api/leave/request", methods=["POST"])
    def leave_request():
        user = _current_user()
        forbidden = _require_api_role(user, EMPLOYEE_ROLES)
        if forbidden:
            return forbidden
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
        forbidden = _require_api_role(user, EMPLOYEE_ROLES)
        if forbidden:
            return forbidden
        mine = [r for r in DEMO_LEAVE_REQUESTS if r.get("employee_email") == user.email]
        mine = sorted(mine, key=lambda r: r.get("created_at", ""), reverse=True)
        return jsonify(ok=True, data=mine), 200

    @app.route("/api/leave/pending", methods=["GET"])
    def leave_pending():
        user = _current_user()
        forbidden = _require_api_role(user, ADMIN_ROLES)
        if forbidden:
            return forbidden
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

    row = _get_user_by_email(email)
    if not row:
        return AuthResult(False, "Akun tidak ditemukan.")
    if int(row["is_active"] or 0) != 1:
        return AuthResult(False, "Akun tidak aktif.")
    if not check_password_hash(row["password_hash"], password):
        return AuthResult(False, "Password salah.")
    user = _user_row_to_user(row, theme)
    _persist_user(user)

    target = "/dashboard/admin" if user.role in ADMIN_ROLES else "/dashboard/pegawai"
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
ADMIN_ROLES = {"hr_superadmin", "manager_operational", "supervisor", "admin_asistent"}
EMPLOYEE_ROLES = {"employee"}
APPROVER_ROLES = {"hr_superadmin", "manager_operational", "supervisor"}
SEED_USERS = [
    {"email": "hr@gmi.com", "name": "HR Superadmin", "role": "hr_superadmin", "password": "hr123456"},
    {"email": "manager@gmi.com", "name": "Manager Ops", "role": "manager_operational", "password": "gmi@12345"},
    {"email": "supervisor@gmi.com", "name": "Supervisor", "role": "supervisor", "password": "gmi@12345"},
    {"email": "asisten@gmi.com", "name": "Admin Asisten", "role": "admin_asistent", "password": "gmi@12345"},
    {"email": "budi@gmi.com", "name": "Budi", "role": "employee", "password": "gmi@12345"},
]
DEFAULT_RESET_PASSWORD = "gmi@12345"
ROLE_OPTIONS = ["hr_superadmin", "manager_operational", "supervisor", "admin_asistent", "employee"]
DEMO_USERS = {}
DEMO_ATTENDANCE = []
DEMO_LEAVE_REQUESTS = []
DEMO_GPS_CENTER = (-6.5706, 107.7603)
DEMO_GPS_RADIUS_METERS = 100
DEMO_QR_PREFIX = "GMI-"


@dataclass
class User:
    id: int
    email: str
    role: str
    name: str = ""
    theme: str = "dark"
    selfie_path: str | None = None
    must_change_password: int = 0


def _role_from_email(email: str) -> str:
    e = email.lower()
    if "manager" in e:
        return "manager_operational"
    if "supervisor" in e:
        return "supervisor"
    if "asisten" in e or "assistant" in e:
        return "admin_asistent"
    if "hr" in e:
        return "hr_superadmin"
    return "employee"


def _persist_user(user: User) -> None:
    session["user"] = {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "name": user.name,
        "theme": user.theme,
        "selfie_path": user.selfie_path,
        "must_change_password": user.must_change_password,
    }


def _current_user() -> User | None:
    data = session.get("user") or {}
    if not data:
        return None
    return User(
        id=int(data.get("id") or 0),
        email=data.get("email", ""),
        role=data.get("role", "employee"),
        name=data.get("name", ""),
        theme=data.get("theme", "dark"),
        selfie_path=data.get("selfie_path"),
        must_change_password=int(data.get("must_change_password") or 0),
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


def _require_manual_approver(user: User | None) -> None:
    if not user or not _can_approve_manual(user):
        abort(403)


def _require_hr_superadmin(user: User | None) -> None:
    _require_role(user, {"hr_superadmin"})


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


def _user_row_to_user(row: sqlite3.Row, theme: str) -> User:
    return User(
        id=int(row["id"]),
        email=row["email"],
        role=row["role"],
        name=row["name"] or "",
        theme=theme,
        selfie_path=row["selfie_path"] if "selfie_path" in row.keys() else None,
        must_change_password=int(row["must_change_password"] or 0),
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


def _create_user(
    name: str,
    email: str,
    role: str,
    password: str,
    is_active: int = 1,
    must_change_password: int = 0,
    selfie_path: str | None = None,
) -> int:
    conn = _db_connect()
    try:
        cur = conn.execute(
            """
            INSERT INTO users (
                name, email, role, password_hash, is_active,
                created_at, updated_at, must_change_password, selfie_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            ),
        )
        return int(cur.lastrowid)
    finally:
        conn.commit()
        conn.close()


def _update_user_basic(user_id: int, name: str, role: str, is_active: int) -> None:
    conn = _db_connect()
    try:
        conn.execute(
            """
            UPDATE users
            SET name = ?, role = ?, is_active = ?, updated_at = ?
            WHERE id = ?
            """,
            (name, role, is_active, _now_ts(), user_id),
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
            SELECT id, name, email, role, is_active, created_at, must_change_password
            FROM users
            ORDER BY created_at DESC
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


def _list_sites() -> list[dict]:
    conn = _db_connect()
    try:
        cur = conn.execute(
            """
            SELECT id, client_name, name, code, location, notes, is_active, created_at
            FROM sites
            ORDER BY created_at DESC
            """
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def _create_site(
    client_name: str,
    name: str,
    code: str | None,
    location: str | None,
    notes: str | None,
) -> None:
    conn = _db_connect()
    try:
        conn.execute(
            """
            INSERT INTO sites (client_name, name, code, location, notes, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (client_name, name, code or None, location or None, notes or None, 1, _now_ts()),
        )
    finally:
        conn.commit()
        conn.close()


def _update_site(
    site_id: int,
    client_name: str,
    name: str,
    code: str | None,
    location: str | None,
    notes: str | None,
) -> None:
    conn = _db_connect()
    try:
        conn.execute(
            """
            UPDATE sites
            SET client_name = ?, name = ?, code = ?, location = ?, notes = ?
            WHERE id = ?
            """,
            (client_name, name, code or None, location or None, notes or None, site_id),
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


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = _table_columns(conn, table)
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {definition}")


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
                selfie_path TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT,
                name TEXT NOT NULL,
                code TEXT UNIQUE,
                location TEXT,
                notes TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT
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
                UNIQUE(supervisor_user_id, site_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS employee_site (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_user_id INTEGER,
                site_id INTEGER,
                UNIQUE(employee_user_id, site_id)
            )
            """
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
            _ensure_column(conn, "sites", "client_name", "client_name TEXT")

        _seed_users(conn)
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
                created_at, updated_at, must_change_password
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
    if user.role == "supervisor":
        return True
    if user.role == "manager_operational":
        return not _has_supervisor_account()
    return False


def _can_approve_leave(user: User) -> bool:
    if user.role not in APPROVER_ROLES:
        return False
    if user.role in {"hr_superadmin"}:
        return True
    if user.role == "supervisor":
        return True
    if user.role == "manager_operational":
        return not _has_supervisor_account()
    return False


def _can_approve_manual(user: User) -> bool:
    if user.role not in APPROVER_ROLES:
        return False
    if user.role in {"hr_superadmin", "supervisor"}:
        return True
    if user.role == "manager_operational":
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
                    WHEN 'manager_operational' THEN 2
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
        return render_template(
            "dashboard/admin_clients.html",
            user=user,
            clients=_clients(),
            sites=_list_sites(),
            shifts=_list_shifts(),
        )

    @bp.route("/employees", methods=["GET"])
    def employees():
        user = _current_user()
        return render_template("dashboard/admin_employees.html", user=user, employees=_employees())

    @bp.route("/attendance", methods=["GET"])
    def attendance():
        user = _current_user()
        return render_template("dashboard/admin_attendance.html", user=user, records=_attendance_live())

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
            can_approve_manual=_can_approve_manual(user),
        )

    @bp.route("/manual_attendance/<int:request_id>/approve", methods=["POST"])
    def manual_attendance_approve(request_id: int):
        user = _current_user()
        _require_manual_approver(user)
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
        _require_manual_approver(user)
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
        _require_hr_superadmin(user)
        tab = (request.args.get("tab") or "users").lower()
        if tab not in {"users", "roles"}:
            tab = "users"
        users = _list_users()
        sites = _list_sites()
        supervisor_sites = _get_supervisor_sites_map()
        return render_template(
            "dashboard/admin_settings.html",
            user=user,
            tab=tab,
            users=users,
            sites=sites,
            supervisor_sites=supervisor_sites,
            role_options=ROLE_OPTIONS,
            default_password=DEFAULT_RESET_PASSWORD,
        )

    @bp.route("/settings/users/create", methods=["POST"])
    def settings_users_create():
        user = _current_user()
        _require_hr_superadmin(user)
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        role = (request.form.get("role") or "employee").strip()
        password = (request.form.get("password") or DEFAULT_RESET_PASSWORD).strip()

        if not _looks_like_email(email):
            flash("Email tidak valid.")
            return redirect(url_for("admin.settings", tab="users"))
        if role not in ROLE_OPTIONS:
            flash("Role tidak valid.")
            return redirect(url_for("admin.settings", tab="users"))
        if role == "hr_superadmin" and _active_hr_superadmin_count():
            flash("HR superadmin aktif sudah ada.")
            return redirect(url_for("admin.settings", tab="users"))
        if _get_user_by_email(email):
            flash("Email sudah terdaftar.")
            return redirect(url_for("admin.settings", tab="users"))

        _create_user(name=name, email=email, role=role, password=password)
        flash("User berhasil ditambahkan.")
        return redirect(url_for("admin.settings", tab="users"))

    @bp.route("/settings/users/<int:user_id>/update", methods=["POST"])
    def settings_users_update(user_id: int):
        user = _current_user()
        _require_hr_superadmin(user)
        name = (request.form.get("name") or "").strip()
        role = (request.form.get("role") or "employee").strip()
        is_active = 1 if request.form.get("is_active") == "1" else 0

        if role not in ROLE_OPTIONS:
            flash("Role tidak valid.")
            return redirect(url_for("admin.settings", tab="users"))
        if user_id == user.id and role != "hr_superadmin":
            flash("HR superadmin tidak boleh mengubah role sendiri.")
            return redirect(url_for("admin.settings", tab="users"))
        if role == "hr_superadmin" and _active_hr_superadmin_count(exclude_user_id=user_id):
            flash("HR superadmin aktif sudah ada.")
            return redirect(url_for("admin.settings", tab="users"))
        if user_id == user.id and is_active == 0:
            flash("HR superadmin tidak boleh dinonaktifkan.")
            return redirect(url_for("admin.settings", tab="users"))

        _update_user_basic(user_id=user_id, name=name, role=role, is_active=is_active)
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
        if user_id == user.id:
            flash("HR superadmin tidak boleh dinonaktifkan.")
            return redirect(url_for("admin.settings", tab="users"))
        is_active = 0 if int(target["is_active"] or 0) == 1 else 1
        if target["role"] == "hr_superadmin" and is_active == 1 and _active_hr_superadmin_count(exclude_user_id=user_id):
            flash("HR superadmin aktif sudah ada.")
            return redirect(url_for("admin.settings", tab="users"))
        _update_user_basic(user_id=user_id, name=target["name"] or "", role=target["role"], is_active=is_active)
        flash("Status user diperbarui.")
        return redirect(url_for("admin.settings", tab="users"))

    @bp.route("/settings/users/<int:user_id>/reset_password", methods=["POST"])
    def settings_users_reset_password(user_id: int):
        user = _current_user()
        _require_hr_superadmin(user)
        hr_password = (request.form.get("hr_password") or "").strip()
        row = _get_user_by_id(user.id)
        if not row or not check_password_hash(row["password_hash"], hr_password):
            flash("Konfirmasi password HR gagal.")
            return redirect(url_for("admin.settings", tab="users"))
        _update_user_password(user_id, DEFAULT_RESET_PASSWORD, 1)
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
        if user_id == user.id:
            flash("HR superadmin tidak boleh menghapus akun sendiri.")
            return redirect(url_for("admin.settings", tab="users"))
        if target["role"] == "hr_superadmin" and int(target["is_active"] or 0) == 1:
            if _active_hr_superadmin_count(exclude_user_id=user_id) == 0:
                flash("HR superadmin terakhir tidak boleh dihapus.")
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
        if target["role"] != "supervisor":
            flash("Assign sites hanya untuk supervisor.")
            return redirect(url_for("admin.settings", tab="users"))
        site_ids = [int(sid) for sid in request.form.getlist("site_ids") if sid.isdigit()]
        _set_supervisor_sites(user_id, site_ids)
        flash("Site assignment diperbarui.")
        return redirect(url_for("admin.settings", tab="users"))

    @bp.route("/settings/sites/create", methods=["POST"])
    def settings_sites_create():
        user = _current_user()
        _require_hr_superadmin(user)
        client_name = (request.form.get("client_name") or "").strip()
        name = (request.form.get("name") or "").strip()
        code = (request.form.get("code") or "").strip()
        location = (request.form.get("location") or "").strip()
        notes = (request.form.get("notes") or "").strip()
        if not client_name:
            flash("Client wajib dipilih.")
            return redirect(url_for("admin.clients", _anchor="sites"))
        if not name:
            flash("Nama site wajib diisi.")
            return redirect(url_for("admin.clients", _anchor="sites"))
        _create_site(client_name=client_name, name=name, code=code, location=location, notes=notes)
        flash("Site berhasil ditambahkan.")
        return redirect(url_for("admin.clients", _anchor="sites"))

    @bp.route("/settings/sites/<int:site_id>/update", methods=["POST"])
    def settings_sites_update(site_id: int):
        user = _current_user()
        _require_hr_superadmin(user)
        client_name = (request.form.get("client_name") or "").strip()
        name = (request.form.get("name") or "").strip()
        code = (request.form.get("code") or "").strip()
        location = (request.form.get("location") or "").strip()
        notes = (request.form.get("notes") or "").strip()
        if not client_name:
            flash("Client wajib dipilih.")
            return redirect(url_for("admin.clients", _anchor="sites"))
        if not name:
            flash("Nama site wajib diisi.")
            return redirect(url_for("admin.clients", _anchor="sites"))
        _update_site(
            site_id=site_id,
            client_name=client_name,
            name=name,
            code=code,
            location=location,
            notes=notes,
        )
        flash("Site berhasil diperbarui.")
        return redirect(url_for("admin.clients", _anchor="sites"))

    @bp.route("/settings/sites/<int:site_id>/toggle", methods=["POST"])
    def settings_sites_toggle(site_id: int):
        user = _current_user()
        _require_hr_superadmin(user)
        current = next((s for s in _list_sites() if int(s["id"]) == site_id), None)
        if not current:
            flash("Site tidak ditemukan.")
            return redirect(url_for("admin.clients", _anchor="sites"))
        is_active = 0 if int(current["is_active"] or 0) == 1 else 1
        _toggle_site(site_id, is_active)
        flash("Status site diperbarui.")
        return redirect(url_for("admin.clients", _anchor="sites"))

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
            return redirect(url_for("admin.clients", _anchor="shifts"))
        _create_shift(name=name, start_time=start_time, end_time=end_time, grace_minutes=grace_minutes)
        flash("Shift berhasil ditambahkan.")
        return redirect(url_for("admin.clients", _anchor="shifts"))

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
            return redirect(url_for("admin.clients", _anchor="shifts"))
        _update_shift(shift_id=shift_id, name=name, start_time=start_time, end_time=end_time, grace_minutes=grace_minutes)
        flash("Shift berhasil diperbarui.")
        return redirect(url_for("admin.clients", _anchor="shifts"))

    @bp.route("/settings/shifts/<int:shift_id>/toggle", methods=["POST"])
    def settings_shifts_toggle(shift_id: int):
        user = _current_user()
        _require_hr_superadmin(user)
        current = next((s for s in _list_shifts() if int(s["id"]) == shift_id), None)
        if not current:
            flash("Shift tidak ditemukan.")
            return redirect(url_for("admin.clients", _anchor="shifts"))
        is_active = 0 if int(current["is_active"] or 0) == 1 else 1
        _toggle_shift(shift_id, is_active)
        flash("Status shift diperbarui.")
        return redirect(url_for("admin.clients", _anchor="shifts"))

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


def _attendance_live(limit: int = 200) -> list[dict]:
    records: list[dict] = []
    conn = _db_connect()
    try:
        if _table_exists(conn, "attendance"):
            cur = conn.execute(
                """
                SELECT employee_name, employee_email, date, time, action, method, source, created_at
                FROM attendance
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            for row in cur.fetchall():
                created_at = row["created_at"] or ""
                date = row["date"] or (created_at.split(" ")[0] if " " in created_at else "-")
                time = row["time"] or (created_at.split(" ")[1] if " " in created_at else "-")
                name = row["employee_name"] or row["employee_email"] or "-"
                raw_source = row["source"] or "sqlite"
                source_label = "demo" if raw_source == "demo" else "sqlite"
                method = row["method"] or ("manual" if raw_source == "manual_request" else "-")
                records.append(
                    {
                        "employee": name,
                        "email": row["employee_email"] or "-",
                        "date": date,
                        "time": time,
                        "action": row["action"] or "-",
                        "method": method,
                        "source": source_label,
                        "created_at": created_at,
                    }
                )
    finally:
        conn.close()

    for r in DEMO_ATTENDANCE:
        if r.get("method") == "manual":
            continue
        created_at = r.get("created_at", "")
        date = created_at.split(" ")[0] if " " in created_at else "-"
        time = created_at.split(" ")[1] if " " in created_at else "-"
        action = r.get("action", "-")
        action_label = "IN" if action == "checkin" else "OUT" if action == "checkout" else action
        records.append(
            {
                "employee": r.get("employee_email", "-"),
                "email": r.get("employee_email", "-"),
                "date": date,
                "time": time,
                "action": action_label,
                "method": r.get("method", "-"),
                "source": "demo",
                "created_at": created_at,
            }
        )

    records = sorted(records, key=lambda row: row.get("created_at", ""), reverse=True)
    return records[:limit]


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5020, debug=False)
else:
    # For WSGI/ASGI servers
    app = create_app()
