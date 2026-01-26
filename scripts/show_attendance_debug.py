import sqlite3

conn = sqlite3.connect('presensi.db')
cursor = conn.cursor()

print('Last 10 attendance records:')
cursor.execute("SELECT id, employee_email, date, time, action, created_at FROM attendance ORDER BY created_at DESC LIMIT 10")
for row in cursor.fetchall():
    print(row)

print('\nAttendance for rahmat@gmail.com on 2026-01-26:')
cursor.execute("SELECT id, employee_email, date, time, action, created_at FROM attendance WHERE employee_email = ? AND date = ?", ('rahmat@gmail.com', '2026-01-26'))
for row in cursor.fetchall():
    print(row)

conn.close()
