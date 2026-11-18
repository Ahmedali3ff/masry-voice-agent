from datetime import date, timedelta

from app.booking import BookingStore

SUNDAY, FRIDAY = 6, 4


def next_weekday(target):
    d = date.today() + timedelta(days=1)
    while d.weekday() != target:
        d += timedelta(days=1)
    return d.isoformat()


def test_weekend_has_no_slots():
    assert BookingStore().available_slots(next_weekday(FRIDAY)) == []


def test_book_removes_slot():
    s = BookingStore()
    day = next_weekday(SUNDAY)
    r = s.book('Ahmed', '01000000000', day, '10:00')
    assert r['ok']
    assert '10:00' not in s.available_slots(day)


def test_double_booking_rejected():
    s = BookingStore()
    day = next_weekday(SUNDAY)
    assert s.book('A', '01000000000', day, '11:00')['ok']
    assert not s.book('B', '01111111111', day, '11:00')['ok']


def test_find_and_cancel():
    s = BookingStore()
    day = next_weekday(SUNDAY)
    bid = s.book('A', '01000000000', day, '12:00')['booking_id']
    assert s.find('01000000000')[0]['booking_id'] == bid
    assert s.cancel(bid)['ok']
    assert s.find('01000000000') == []


def test_bad_date():
    assert BookingStore().available_slots('not-a-date') == []
