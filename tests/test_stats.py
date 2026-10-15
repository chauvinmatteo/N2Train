from datetime import timedelta

from fsrs import Rating

import srs
import stats
from dates import to_iso, utc_now


def test_streak_counts_consecutive_days():

    now = utc_now()
    days = [to_iso(now - timedelta(days=d)) for d in (0, 1, 2, 4)]
    assert stats.streak(days, now) == 3


def test_streak_survives_until_the_end_of_today():

    now = utc_now()
    assert stats.streak([to_iso(now - timedelta(days=1))], now) == 1
    assert stats.streak([to_iso(now - timedelta(days=2))], now) == 0


def test_forecast_puts_overdue_kanji_today():

    now = utc_now()
    kanjis = [{"due": to_iso(now - timedelta(days=3))},
              {"due": to_iso(now + timedelta(days=2))},
              {"due": to_iso(now + timedelta(days=40))},
              {"due": None}]
    values = stats.forecast(kanjis, now)
    assert values[0] == 1 and sum(values) == 2


def test_compute_on_a_fresh_deck(db):

    data = stats.compute(db, utc_now())
    assert data.total == 367
    assert data.levels == {"new": 367, "learning": 0, "young": 0,
                           "mature": 0}
    assert data.accuracy_week is None


def test_compute_after_a_review(db):

    now = utc_now()
    kanji = db.new_kanji(1)[0]
    card = srs.review(srs.load_card(None, kanji["id"]), Rating.Again, now)
    db.save_review(kanji["id"], card, "reading", False, Rating.Again, now)
    data = stats.compute(db, now)
    assert data.levels["learning"] == 1
    assert data.missed[0]["caractere"] == kanji["caractere"]
    assert data.streak == 1
