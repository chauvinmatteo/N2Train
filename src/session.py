import random
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta

from fsrs import Card, Rating

import srs
from database import Database
from dates import local_day_start, utc_now
from quiz import Question, make_question

NEW_PER_DAY = 15
# A failed kanji due again within this delay comes back in the same session
LEARN_AHEAD = timedelta(minutes=20)


@dataclass
class Result:

    kanji: dict
    correct: bool
    rating: Rating


class Session:

    def __init__(self, db: Database, size: int,
                 rng: random.Random | None = None,
                 now: datetime | None = None) -> None:

        now = now or utc_now()
        self.db = db
        self.rng = rng or random.Random()
        self.started_at = now

        due = db.due_kanji(now, size)
        introduced = db.count_introduced_since(local_day_start(now))
        new_left = max(0, NEW_PER_DAY - introduced)
        new = db.new_kanji(min(new_left, size - len(due)))
        items = due + new
        self.rng.shuffle(items)

        self.queue: deque[dict] = deque(items)
        self.results: list[Result] = []
        self.kanji: dict | None = None
        self.card: Card | None = None
        self.question: Question | None = None
        self.duration_ms: int | None = None

    @property
    def done(self) -> int:

        return len(self.results)

    @property
    def total(self) -> int:

        pending = 1 if self.question is not None else 0
        return self.done + pending + len(self.queue)

    def next_question(self) -> Question | None:

        if not self.queue:
            self.kanji = self.card = self.question = None
            return None
        self.kanji = self.queue.popleft()
        self.card = srs.load_card(self.kanji["card"], self.kanji["id"])
        self.question = make_question(self.kanji, self.db.distractors,
                                      self.rng)
        return self.question

    def answer(self, index: int, duration_ms: int | None = None) -> bool:

        assert self.question is not None
        self.duration_ms = duration_ms
        correct = index == self.question.answer_index
        if not correct:
            self.grade(Rating.Again)
        return correct

    def intervals(self) -> dict[Rating, timedelta]:

        assert self.card is not None
        return srs.preview(self.card)

    def grade(self, rating: Rating, now: datetime | None = None) -> None:

        assert self.kanji is not None and self.card is not None
        assert self.question is not None
        now = now or utc_now()
        card = srs.review(self.card, rating, now, self.duration_ms)
        correct = rating != Rating.Again
        self.db.save_review(self.kanji["id"], card, self.question.kind,
                            correct, rating, now, self.duration_ms)
        self.results.append(Result(self.kanji, correct, rating))

        if card.due <= now + LEARN_AHEAD:
            self.queue.append({**self.kanji, "card": card.to_json()})
        self.question = None

    def accuracy(self) -> float:

        if not self.results:
            return 0.0
        return sum(r.correct for r in self.results) / len(self.results)

    def missed(self) -> list[dict]:

        seen: dict[int, dict] = {}
        for result in self.results:
            if not result.correct:
                seen.setdefault(result.kanji["id"], result.kanji)
        return list(seen.values())
