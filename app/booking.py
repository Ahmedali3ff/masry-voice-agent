import secrets
import sqlite3
from datetime import date

WORK_HOURS = [f'{h:02d}:00' for h in range(10, 18)]
WEEKEND = {4, 5}  # Friday, Saturday


class BookingStore:
    def __init__(self, path=':memory:'):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.execute(
            'CREATE TABLE IF NOT EXISTS appointments ('
            'id TEXT PRIMARY KEY, name TEXT, phone TEXT, day TEXT, slot TEXT, '
            'UNIQUE(day, slot))'
        )
        self.conn.commit()

    @staticmethod
    def _parse(day):
        try:
            return date.fromisoformat(day)
        except (ValueError, TypeError):
            return None

    def available_slots(self, day):
        d = self._parse(day)
        if d is None or d < date.today() or d.weekday() in WEEKEND:
            return []
        rows = self.conn.execute('SELECT slot FROM appointments WHERE day=?', (day,))
        taken = {r[0] for r in rows}
        return [s for s in WORK_HOURS if s not in taken]

    def book(self, name, phone, day, slot):
        if slot not in self.available_slots(day):
            return {'ok': False, 'error': 'slot_unavailable'}
        booking_id = secrets.token_hex(3).upper()
        try:
            self.conn.execute(
                'INSERT INTO appointments VALUES (?,?,?,?,?)',
                (booking_id, name, phone, day, slot),
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            return {'ok': False, 'error': 'slot_unavailable'}
        return {'ok': True, 'booking_id': booking_id, 'day': day, 'slot': slot}

    def find(self, phone):
        rows = self.conn.execute(
            'SELECT id, day, slot FROM appointments '
            'WHERE phone=? AND day>=? ORDER BY day, slot',
            (phone, date.today().isoformat()),
        )
        return [{'booking_id': r[0], 'day': r[1], 'slot': r[2]} for r in rows]

    def cancel(self, booking_id):
        cur = self.conn.execute(
            'DELETE FROM appointments WHERE id=?', (str(booking_id).upper(),)
        )
        self.conn.commit()
        return {'ok': cur.rowcount > 0}
