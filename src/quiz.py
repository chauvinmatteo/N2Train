import random
from dataclasses import dataclass
from typing import Callable

# kind: (japanese label, english label, question asked)
QUESTION_TYPES: dict[str, tuple[str, str, str]] = {
    "meaning": ("意味", "Meaning", "What does this kanji mean?"),
    "reading": ("読み方", "Reading", "How is this kanji read?"),
    "caractere": ("書き方", "Writing", "Which kanji matches this meaning?"),
}

DistractorFn = Callable[[str, str], list[str]]


@dataclass(frozen=True)
class Question:

    kind: str
    label_jp: str
    label: str
    hint: str
    prompt: str
    prompt_is_kanji: bool
    choices: list[str]
    choice_style: str
    answer_index: int


def to_katakana(text: str) -> str:

    return "".join(chr(ord(c) + 0x60) if "ぁ" <= c <= "ゖ" else c
                   for c in text)


def format_reading(raw: str) -> str:

    # The CSV uses the KANJIDIC style "on | kun", with "-" when one is empty.
    # On'yomi is displayed in katakana, kun'yomi in hiragana, as in
    # dictionaries.
    on, _, kun = raw.partition("|")
    on_readings = [to_katakana(r) for r in on.split() if r != "-"]
    kun_readings = [r for r in kun.split() if r != "-"]
    lines = ["、".join(group) for group in (on_readings, kun_readings)
             if group]
    return "\n".join(lines)


def display_value(kind: str, value: str) -> str:

    return format_reading(value) if kind == "reading" else value


def make_question(kanji: dict, distractors_for: DistractorFn,
                  rng: random.Random | None = None) -> Question:

    rng = rng or random.Random()
    kind = rng.choice(list(QUESTION_TYPES))
    label_jp, label, hint = QUESTION_TYPES[kind]

    good_answer: str = kanji[kind]
    choices = [good_answer] + distractors_for(kind, good_answer)
    rng.shuffle(choices)

    if kind == "caractere":
        prompt, prompt_is_kanji = kanji["meaning"], False
        choice_style = "kanji"
    else:
        prompt, prompt_is_kanji = kanji["caractere"], True
        choice_style = "kana" if kind == "reading" else "text"

    return Question(
        kind=kind,
        label_jp=label_jp,
        label=label,
        hint=hint,
        prompt=prompt,
        prompt_is_kanji=prompt_is_kanji,
        choices=[display_value(kind, c) for c in choices],
        choice_style=choice_style,
        answer_index=choices.index(good_answer),
    )
