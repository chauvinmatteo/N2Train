from fsrs import Rating, State

import srs


def test_new_card_uses_kanji_id():

    card = srs.load_card(None, 42)
    assert card.card_id == 42
    assert srs.card_level(None) == "new"


def test_card_json_round_trip():

    card = srs.review(srs.load_card(None, 1), Rating.Good)
    assert srs.load_card(card.to_json(), 1).due == card.due


def test_better_ratings_give_longer_intervals():

    card = srs.load_card(None, 1)
    intervals = srs.preview(card)
    assert intervals[Rating.Hard] <= intervals[Rating.Good]
    assert intervals[Rating.Good] < intervals[Rating.Easy]


def test_easy_graduates_a_new_card():

    card = srs.review(srs.load_card(None, 1), Rating.Easy)
    assert card.state == State.Review
    assert srs.card_level(card) == "young"


def test_failure_sends_a_known_card_back_to_learning():

    card = srs.review(srs.load_card(None, 1), Rating.Easy)
    card = srs.review(card, Rating.Again, card.due)
    assert card.state == State.Relearning
    assert srs.card_level(card) == "learning"
