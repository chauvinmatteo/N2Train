from datetime import timedelta

import pytest
from fsrs import Rating

import srs
from dates import utc_now


def test_seed_is_idempotent(db, tmp_path):

    from conftest import CSV_PATH
    assert db.count_new() == 367
    assert db.seed(CSV_PATH) == 0


@pytest.mark.parametrize("column", ["caractere", "meaning", "reading"])
def test_distractors_never_match_the_answer(db, column):

    for kanji in db.all_kanji():
        values = db.distractors(column, kanji[column])
        assert len(values) == 3
        assert len(set(values)) == 3
        assert kanji[column] not in values


def test_distractors_reject_unknown_columns(db):

    with pytest.raises(ValueError):
        db.distractors("id; DROP TABLE kanjis", "x")


def test_save_review_schedules_the_kanji(db):

    now = utc_now()
    kanji = db.new_kanji(1)[0]
    card = srs.review(srs.load_card(None, kanji["id"]), Rating.Easy, now)
    db.save_review(kanji["id"], card, "meaning", True, Rating.Easy, now)

    assert db.count_new() == 366
    assert db.count_due(now) == 0
    assert db.count_due(card.due + timedelta(seconds=1)) == 1
    assert db.count_introduced_since(now - timedelta(minutes=1)) == 1
    assert db.accuracy_since() == (1, 1)
