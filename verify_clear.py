import sqlite3

conn = sqlite3.connect('presensi.db')
cur = conn.execute('SELECT COUNT(*) as total FROM attendance WHERE date = "2026-01-25"')
row = cur.fetchone()
print(f'✓ Total attendance records untuk 2026-01-25: {row[0]}')

cur = conn.execute('SELECT COUNT(*) as total FROM attendance')
row = cur.fetchone()
print(f'✓ Total attendance records keseluruhan: {row[0]}')

deleted = 0
if row[0] > 0:
	cur = conn.execute('DELETE FROM attendance')
	deleted = conn.total_changes
	conn.commit()
	print(f'✓ Deleted {deleted} attendance record(s)')
else:
	print('✓ Tidak ada record attendance yang dihapus')
conn.close()
