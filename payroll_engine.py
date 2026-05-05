from __future__ import annotations

import json
from typing import Any


PAYROLL_ENGINE_VERSION = "payroll_engine_v1"
PAYROLL_MODE_STANDARD = "standard"
PAYROLL_MODE_ADVANCED = "advanced"
BPJS_KESEHATAN_KEYS = {"kesehatan"}


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def calculate_basic_salary(attendance_summary: dict[str, Any], config: dict[str, Any]) -> dict[str, float]:
    salary_base = _number(config.get("salary_base"))
    working_days = max(1, _int(attendance_summary.get("working_days")))
    attendance_days = _int(attendance_summary.get("attendance_days"))
    daily_rate = salary_base / working_days
    scheme = config.get("payroll_scheme") or "PRORATED_ATTENDANCE"
    if scheme == "FULL_MONTHLY_DEDUCTION":
        gross_salary = salary_base
    else:
        gross_salary = attendance_days * daily_rate
    return {
        "salary_base": salary_base,
        "working_days": working_days,
        "attendance_days": attendance_days,
        "daily_rate": daily_rate,
        "gross_salary": gross_salary,
    }


def calculate_attendance_deductions(attendance_summary: dict[str, Any], config: dict[str, Any], basic: dict[str, float]) -> dict[str, float]:
    late_days = _int(attendance_summary.get("late_days"))
    absent_days = _int(attendance_summary.get("absent_days"))
    late_rate = _number(config.get("potongan_telat_rate"))
    absent_rate = _number(config.get("potongan_absen_rate"))
    scheme = config.get("payroll_scheme") or "PRORATED_ATTENDANCE"
    absent_deduction = absent_days * basic["daily_rate"] if scheme == "FULL_MONTHLY_DEDUCTION" else 0.0
    return {
        "late_days": late_days,
        "absent_days": absent_days,
        "late_deduction_rate": late_rate,
        "absent_deduction_rate": absent_rate,
        "potongan_telat": late_days * late_rate,
        "potongan_absen": absent_deduction,
    }


def calculate_allowances(config: dict[str, Any]) -> dict[str, Any]:
    items = config.get("allowances") if isinstance(config.get("allowances"), dict) else {}
    total = sum(_number(value) for value in items.values())
    total += _number(config.get("tunjangan"))
    return {"items": items, "total": total}


def calculate_custom_deductions(config: dict[str, Any]) -> dict[str, Any]:
    items = config.get("deductions") if isinstance(config.get("deductions"), dict) else {}
    total = sum(_number(value) for value in items.values())
    total += _number(config.get("potongan_lain"))
    return {"items": items, "total": total}


def calculate_bpjs(config: dict[str, Any], gross_salary: float) -> dict[str, Any]:
    if not config.get("bpjs_enabled"):
        return {"enabled": False, "employee_total": 0.0, "company_total": 0.0, "items": {}}
    rates = config.get("bpjs_rates") if isinstance(config.get("bpjs_rates"), dict) else {}
    caps = config.get("bpjs_caps") if isinstance(config.get("bpjs_caps"), dict) else {}
    kesehatan_enabled = config.get("bpjs_kesehatan_enabled", True) is not False
    tk_enabled = config.get("bpjs_tk_enabled", True) is not False
    employee_items: dict[str, float] = {}
    company_items: dict[str, float] = {}
    for key, rate in rates.get("employee", {}).items() if isinstance(rates.get("employee"), dict) else []:
        if (key in BPJS_KESEHATAN_KEYS and not kesehatan_enabled) or (key not in BPJS_KESEHATAN_KEYS and not tk_enabled):
            continue
        cap = _number(caps.get(key), gross_salary)
        base = min(gross_salary, cap) if cap > 0 else gross_salary
        employee_items[key] = base * _number(rate)
    for key, rate in rates.get("company", {}).items() if isinstance(rates.get("company"), dict) else []:
        if (key in BPJS_KESEHATAN_KEYS and not kesehatan_enabled) or (key not in BPJS_KESEHATAN_KEYS and not tk_enabled):
            continue
        cap = _number(caps.get(key), gross_salary)
        base = min(gross_salary, cap) if cap > 0 else gross_salary
        company_items[key] = base * _number(rate)
    return {
        "enabled": True,
        "kesehatan_enabled": kesehatan_enabled,
        "tk_enabled": tk_enabled,
        "employee_total": sum(employee_items.values()),
        "company_total": sum(company_items.values()),
        "items": {
            "employee": employee_items,
            "company": company_items,
        },
    }


def calculate_tax_pph21(config: dict[str, Any], gross_salary: float, deductions_before_tax: float) -> dict[str, Any]:
    if not config.get("tax_enabled"):
        return {"enabled": False, "status": config.get("tax_status") or "", "monthly_tax": 0.0}
    override = config.get("monthly_tax_override")
    if override not in (None, ""):
        monthly_tax = max(0.0, _number(override))
        return {
            "enabled": True,
            "status": config.get("tax_status") or "TK0",
            "method": "manual_override",
            "monthly_tax": monthly_tax,
            "taxable_estimate": max(0.0, gross_salary - deductions_before_tax),
        }
    status = str(config.get("tax_status") or "TK0").replace("/", "").upper()
    ptkp_map = config.get("ptkp") if isinstance(config.get("ptkp"), dict) else {}
    brackets = config.get("tax_brackets") if isinstance(config.get("tax_brackets"), list) else []
    occupational_rate = max(0.0, _number(config.get("occupational_expense_rate"), 0.0))
    occupational_cap = max(0.0, _number(config.get("occupational_expense_monthly_cap"), 0.0))
    occupational_expense = gross_salary * occupational_rate
    if occupational_cap:
        occupational_expense = min(occupational_expense, occupational_cap)
    monthly_taxable_estimate = max(0.0, gross_salary - deductions_before_tax - occupational_expense)
    annual_taxable = max(0.0, monthly_taxable_estimate * 12 - _number(ptkp_map.get(status)))
    annual_taxable = _round_down_thousand(annual_taxable) if config.get("round_pkp_thousand", True) else annual_taxable
    annual_tax = _progressive_tax(annual_taxable, brackets)
    monthly_tax = annual_tax / 12
    return {
        "enabled": True,
        "status": status,
        "method": "annualized_simplified",
        "monthly_tax": monthly_tax,
        "annual_tax": annual_tax,
        "annual_taxable": annual_taxable,
        "ptkp": _number(ptkp_map.get(status)),
        "gross_monthly_taxable_base": gross_salary,
        "deductions_before_tax": deductions_before_tax,
        "occupational_expense": occupational_expense,
        "taxable_estimate": monthly_taxable_estimate,
        "disclaimer": "Estimasi PPh21 sederhana, bukan bukti potong atau final tax filing.",
    }


def _round_down_thousand(value: float) -> float:
    return float(int(max(0.0, value) // 1000) * 1000)


def _progressive_tax(taxable: float, brackets: list[Any]) -> float:
    remaining = max(0.0, taxable)
    previous_limit = 0.0
    total = 0.0
    for bracket in brackets:
        if not isinstance(bracket, dict):
            continue
        limit_raw = bracket.get("limit")
        limit = None if limit_raw in (None, "", "inf") else _number(limit_raw)
        rate = _number(bracket.get("rate"))
        span = remaining if limit is None else max(0.0, min(remaining, limit - previous_limit))
        total += span * rate
        remaining -= span
        if limit is not None:
            previous_limit = limit
        if remaining <= 0:
            break
    return max(0.0, total)


def calculate_thr(config: dict[str, Any]) -> dict[str, Any]:
    if not config.get("is_thr_period") and not _number(config.get("thr_amount")):
        return {"enabled": False, "amount": 0.0}
    manual_amount = config.get("thr_amount")
    if manual_amount not in (None, ""):
        amount = max(0.0, _number(manual_amount))
        return {"enabled": amount > 0, "method": "manual_override", "amount": amount}
    salary_base = max(0.0, _number(config.get("salary_base")))
    multiplier = max(0.0, _number(config.get("thr_base_multiplier"), 1.0))
    tenure_months = max(0.0, _number(config.get("tenure_months"), 12.0))
    prorate = min(1.0, tenure_months / 12.0)
    amount = salary_base * multiplier * prorate
    return {
        "enabled": amount > 0,
        "method": "prorate" if prorate < 1 else "full",
        "tenure_months": tenure_months,
        "base_multiplier": multiplier,
        "prorate": prorate,
        "amount": amount,
    }


def calculate_overtime(config: dict[str, Any]) -> dict[str, Any]:
    hours = max(0.0, _number(config.get("overtime_hours")))
    rate = max(0.0, _number(config.get("overtime_rate")))
    multiplier = max(0.0, _number(config.get("overtime_multiplier"), 1.0))
    manual_amount = config.get("overtime_amount")
    if manual_amount not in (None, ""):
        amount = max(0.0, _number(manual_amount))
        return {"enabled": amount > 0, "method": "manual_override", "hours": hours, "rate": rate, "multiplier": multiplier, "amount": amount}
    amount = hours * rate * multiplier
    return {"enabled": amount > 0, "method": "hours_rate", "hours": hours, "rate": rate, "multiplier": multiplier, "amount": amount}


def calculate_net_salary(gross: float, allowances: float, deductions: float, bpjs_employee: float, tax: float, thr: float, overtime: float) -> float:
    return max(0.0, gross + allowances + thr + overtime - deductions - bpjs_employee - tax)


def run_payroll_engine(employee: dict[str, Any], attendance_summary: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    mode = config.get("payroll_mode") or PAYROLL_MODE_STANDARD
    scheme = config.get("payroll_scheme") or "PRORATED_ATTENDANCE"
    basic = calculate_basic_salary(attendance_summary, {**config, "payroll_scheme": scheme})
    attendance_deductions = calculate_attendance_deductions(attendance_summary, {**config, "payroll_scheme": scheme}, basic)
    allowances = calculate_allowances(config)
    custom_deductions = calculate_custom_deductions(config)
    bpjs = calculate_bpjs(config, basic["gross_salary"]) if mode == PAYROLL_MODE_ADVANCED else calculate_bpjs({}, basic["gross_salary"])
    thr = calculate_thr(config) if mode == PAYROLL_MODE_ADVANCED else calculate_thr({})
    overtime = calculate_overtime(config) if mode == PAYROLL_MODE_ADVANCED else calculate_overtime({})
    taxable_gross = basic["gross_salary"] + allowances["total"] + thr["amount"] + overtime["amount"]
    tax = calculate_tax_pph21(config, taxable_gross, bpjs["employee_total"]) if mode == PAYROLL_MODE_ADVANCED else calculate_tax_pph21({}, taxable_gross, 0.0)
    total_deductions = attendance_deductions["potongan_telat"] + attendance_deductions["potongan_absen"] + custom_deductions["total"]
    net = calculate_net_salary(
        basic["gross_salary"],
        allowances["total"],
        total_deductions,
        bpjs["employee_total"],
        tax["monthly_tax"],
        thr["amount"],
        overtime["amount"],
    )
    breakdown = {
        "version": PAYROLL_ENGINE_VERSION,
        "mode": mode,
        "employee": {
            "email": employee.get("email") or employee.get("employee_email") or "",
            "name": employee.get("name") or employee.get("employee_name") or "",
        },
        "attendance": {
            "attendance_days": basic["attendance_days"],
            "working_days": basic["working_days"],
            "late_days": attendance_deductions["late_days"],
            "absent_days": attendance_deductions["absent_days"],
            "leave_days": _int(attendance_summary.get("leave_days")),
        },
        "basic_salary": basic,
        "allowances": allowances,
        "deductions": {
            **attendance_deductions,
            "custom": custom_deductions,
            "total": total_deductions,
        },
        "bpjs": bpjs,
        "tax": tax,
        "thr": thr,
        "overtime": overtime,
        "gross": basic["gross_salary"],
        "total_deductions": total_deductions + bpjs["employee_total"] + tax["monthly_tax"],
        "net": net,
    }
    return {
        "salary_base": basic["salary_base"],
        "attendance_days": basic["attendance_days"],
        "late_days": attendance_deductions["late_days"],
        "absent_days": attendance_deductions["absent_days"],
        "leave_days": _int(attendance_summary.get("leave_days")),
        "working_days": basic["working_days"],
        "potongan_telat": attendance_deductions["potongan_telat"],
        "potongan_absen": attendance_deductions["potongan_absen"],
        "potongan_lain": custom_deductions["total"],
        "tunjangan": allowances["total"],
        "total_gaji": net,
        "daily_rate": basic["daily_rate"],
        "gross_salary": basic["gross_salary"],
        "late_deduction_rate": attendance_deductions["late_deduction_rate"],
        "absent_deduction_rate": attendance_deductions["absent_deduction_rate"],
        "payroll_mode": mode,
        "engine_version": PAYROLL_ENGINE_VERSION,
        "breakdown": breakdown,
    }


def update_payroll_breakdown_adjustments(breakdown: dict[str, Any] | None, potongan_lain: float, tunjangan: float) -> dict[str, Any]:
    updated = dict(breakdown or {})
    allowances = dict(updated.get("allowances") or {})
    deductions = dict(updated.get("deductions") or {})
    custom = dict(deductions.get("custom") or {})
    custom["total"] = max(0.0, _number(potongan_lain))
    allowances["total"] = max(0.0, _number(tunjangan))
    deductions["custom"] = custom
    attendance_total = _number(deductions.get("potongan_telat")) + _number(deductions.get("potongan_absen"))
    deductions["total"] = attendance_total + custom["total"]
    gross = _number(updated.get("gross"))
    bpjs_employee = _number((updated.get("bpjs") or {}).get("employee_total") if isinstance(updated.get("bpjs"), dict) else 0)
    tax = _number((updated.get("tax") or {}).get("monthly_tax") if isinstance(updated.get("tax"), dict) else 0)
    thr = _number((updated.get("thr") or {}).get("amount") if isinstance(updated.get("thr"), dict) else 0)
    overtime = _number((updated.get("overtime") or {}).get("amount") if isinstance(updated.get("overtime"), dict) else 0)
    updated["allowances"] = allowances
    updated["deductions"] = deductions
    updated["total_deductions"] = deductions["total"] + bpjs_employee + tax
    updated["net"] = calculate_net_salary(gross, allowances["total"], deductions["total"], bpjs_employee, tax, thr, overtime)
    return updated


def dumps_breakdown(breakdown: dict[str, Any] | None) -> str:
    return json.dumps(breakdown or {}, ensure_ascii=False, sort_keys=True)


def loads_breakdown(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    try:
        parsed = json.loads(str(value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}
