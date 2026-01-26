#!/usr/bin/env python3
"""Test script to debug /api/attendance/today endpoint"""

import sqlite3
import json
from datetime import datetime, date

conn = sqlite3.connect('presensi.db')
conn.row_factory = sqlite3.Row

# Get today's date
today = date.today().strftime("%Y-%m-%d")
print(f"Today's date: {today}")

# Query attendance records
cur = conn.execute("""
    SELECT id, employee_email, date, time, action, method, created_at
    FROM attendance
    WHERE date = ?
    ORDER BY created_at DESC
    LIMIT 10
""", (today,))

records = [dict(row) for row in cur.fetchall()]
print(f"\nTotal records for {today}: {len(records)}")

for i, rec in enumerate(records):
    print(f"\nRecord {i+1}:")
    print(f"  action: {rec['action']}")
    print(f"  time: {rec['time']}")
    print(f"  method: {rec['method']}")
    print(f"  created_at: {rec['created_at']}")

# Simulate API response
response = {"ok": True, "data": records}
print(f"\nAPI Response (JSON):")
print(json.dumps(response, indent=2))

conn.close()
