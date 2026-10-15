import random

from quiz import format_reading, make_question, to_katakana

KANJI = {"id": 1, "caractere": "丸", "meaning": "Round / Full (month)",
         "reading": "がん | まる まる.める"}


def fake_distractors(kind, good):

    return [f"{kind}-{i}" for i in range(3)]


def test_to_katakana():

    assert to_katakana("がん") == "ガン"
    assert to_katakana("ガン") == "ガン"


def test_format_reading():

    assert format_reading("がん | まる まる.める") == "ガン\nまる、まる.める"
    assert format_reading("りょう | -") == "リョウ"
    assert format_reading("- | まれ") == "まれ"


def test_question_contains_the_answer_once():

    for seed in range(30):
        q = make_question(KANJI, fake_distractors, random.Random(seed))
        assert len(q.choices) == 4
        assert len(set(q.choices)) == 4
        good = q.choices[q.answer_index]
        if q.kind == "meaning":
            assert good == KANJI["meaning"] and q.prompt == "丸"
        elif q.kind == "caractere":
            assert good == "丸" and q.prompt == KANJI["meaning"]
        else:
            assert good == "ガン\nまる、まる.める" and q.prompt == "丸"
