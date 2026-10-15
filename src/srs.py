from datetime import datetime, timedelta

from fsrs import Card, Rating, Scheduler, State

from dates import utc_now

# Probability of remembering a kanji when it comes back for review
DESIRED_RETENTION = 0.9
# A kanji whose memory lasts at least this long is considered mastered
MATURE_STABILITY = 21

scheduler = Scheduler(desired_retention=DESIRED_RETENTION)


def load_card(card_json: str | None, kanji_id: int) -> Card:

    if card_json is None:
        return Card(card_id=kanji_id)
    return Card.from_json(card_json)


def review(card: Card, rating: Rating, now: datetime | None = None,
           duration_ms: int | None = None) -> Card:

    new_card, _ = scheduler.review_card(card, rating,
                                        review_datetime=now or utc_now(),
                                        review_duration=duration_ms)
    return new_card


def preview(card: Card, now: datetime | None = None) -> dict[Rating,
                                                             timedelta]:

    now = now or utc_now()
    return {rating: review(card, rating, now).due - now
            for rating in (Rating.Hard, Rating.Good, Rating.Easy)}


def card_level(card: Card | None) -> str:

    if card is None:
        return "new"
    if card.state != State.Review:
        return "learning"
    if (card.stability or 0) >= MATURE_STABILITY:
        return "mature"
    return "young"
