import random

from fsrs import Rating

from session import NEW_PER_DAY, Session


def answer_right(session):

    session.answer(session.question.answer_index)


def answer_wrong(session):

    session.answer((session.question.answer_index + 1) % 4)


def test_new_kanji_are_limited_per_day(db):

    session = Session(db, 50, random.Random(0))
    assert session.total == NEW_PER_DAY


def test_session_is_smaller_than_the_requested_size(db):

    assert Session(db, 5, random.Random(0)).total == 5


def test_easy_answers_finish_the_session(db):

    session = Session(db, 5, random.Random(0))
    while session.next_question():
        answer_right(session)
        session.grade(Rating.Easy)
    assert session.done == 5
    assert session.accuracy() == 1.0
    assert db.count_new() == 362


def test_mistakes_come_back_in_the_same_session(db):

    session = Session(db, 1, random.Random(0))
    session.next_question()
    answer_wrong(session)
    assert session.done == 1 and len(session.queue) == 1
    assert len(session.missed()) == 1
    assert db.accuracy_since() == (0, 1)


def test_new_limit_counts_kanji_from_earlier_sessions(db):

    first = Session(db, 5, random.Random(0))
    while first.next_question():
        answer_right(first)
        first.grade(Rating.Easy)
    second = Session(db, 50, random.Random(0))
    assert second.total == NEW_PER_DAY - 5
