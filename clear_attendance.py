import sqlite3
from datetime import datetime

conn = sqlite3.connect('presensi.db')
cursor = conn.cursor()

# Get attendance table schema
cursor.execute("PRAGMA table_info(attendance)")
columns = cursor.fetchall()

print('Attendance table columns:')
for col in columns:
    print(f'  {col[1]} ({col[2]})')

# Get a few records to see structure
cursor.execute('SELECT * FROM attendance LIMIT 1')
records = cursor.fetchall()
if records:
    print(f'\nSample record:')
    print(f'  {records[0]}')

# Now delete today's records for baim@gmail.com
today = datetime.now().strftime('%Y-%m-%d')
print(f'\nDeleting attendance records for {today}...')

cursor.execute("SELECT * FROM attendance WHERE created_at LIKE ? LIMIT 5", (f'{today}%',))
records = cursor.fetchall()
print(f'Records to delete:')
for rec in records:
    print(f'  {rec}')

cursor.execute("DELETE FROM attendance WHERE created_at LIKE ?", (f'{today}%',))
deleted = cursor.rowcount
conn.commit()
print(f'\nDeleted {deleted} record(s)')

conn.close()
