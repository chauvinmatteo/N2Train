from dataclasses import dataclass
from datetime import date, datetime, timedelta

import srs
from database import Database
from dates import from_iso, local_day_start

LEVELS = ("new", "learning", "young", "mature")


@dataclass
class Stats:

    total: int
    levels: dict[str, int]
    forecast: list[int]
    streak: int
    reviews_total: int
    accuracy_week: float | None
    reviews_today: int
    missed: list[dict]


def level_counts(kanjis: list[dict]) -> dict[str, int]:

    counts = dict.fromkeys(LEVELS, 0)
    for kanji in kanjis:
        card = srs.load_card(kanji["card"], kanji["id"]) \
            if kanji["card"] else None
        counts[srs.card_level(card)] += 1
    return counts


def forecast(kanjis: list[dict], now: datetime, days: int = 14) -> list[int]:

    # Index 0 is today, overdue kanji included
    today = now.astimezone().date()
    counts = [0] * days
    for kanji in kanjis:
        if kanji["due"] is None:
            continue
        offset = (from_iso(kanji["due"]).astimezone().date() - today).days
        if offset < days:
            counts[max(0, offset)] += 1
    return counts


def streak(review_dates: list[str], now: datetime) -> int:

    days = {from_iso(d).astimezone().date() for d in review_dates}
    today: date = now.astimezone().date()
    # Today without reviews yet doesn't break the streak
    current = today if today in days else today - timedelta(days=1)
    count = 0
    while current in days:
        count += 1
        current -= timedelta(days=1)
    return count


def compute(db: Database, now: datetime) -> Stats:

    kanjis = db.all_kanji()
    day_start = local_day_start(now)
    correct_week, total_week = db.accuracy_since(day_start
                                                 - timedelta(days=6))
    _, reviews_total = db.accuracy_since()
    _, reviews_today = db.accuracy_since(day_start)

    return Stats(
        total=len(kanjis),
        levels=level_counts(kanjis),
        forecast=forecast(kanjis, now),
        streak=streak(db.review_dates(), now),
        reviews_total=reviews_total,
        accuracy_week=correct_week / total_week if total_week else None,
        reviews_today=reviews_today,
        missed=db.most_missed(),
    )
