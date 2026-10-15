from datetime import datetime, timedelta, timezone

from dates import format_interval, from_iso, to_iso


def test_iso_round_trip_is_utc():

    moment = datetime(2026, 10, 14, 12, 0, tzinfo=timezone.utc)
    assert from_iso(to_iso(moment)) == moment
    assert to_iso(moment).endswith("+00:00")


def test_iso_strings_sort_like_dates():

    base = datetime(2026, 10, 14, 12, 0, tzinfo=timezone.utc)
    later = base + timedelta(microseconds=1)
    assert to_iso(base) < to_iso(later)


def test_format_interval():

    assert format_interval(timedelta(seconds=10)) == "now"
    assert format_interval(timedelta(minutes=10)) == "10 min"
    assert format_interval(timedelta(hours=5)) == "5 h"
    assert format_interval(timedelta(days=3)) == "3 d"
    assert format_interval(timedelta(days=90)) == "3 mo"
