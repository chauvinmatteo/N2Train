from datetime import datetime, timedelta, timezone


def utc_now() -> datetime:

    return datetime.now(timezone.utc)


def to_iso(moment: datetime) -> str:

    # Fixed format so that dates stored in SQLite compare correctly as text
    return moment.astimezone(timezone.utc).isoformat(timespec="microseconds")


def from_iso(text: str) -> datetime:

    return datetime.fromisoformat(text)


def local_day_start(moment: datetime) -> datetime:

    local = moment.astimezone()
    return local.replace(hour=0, minute=0, second=0, microsecond=0)


def format_interval(delay: timedelta) -> str:

    seconds = max(0, int(delay.total_seconds()))
    if seconds < 60:
        return "now"
    if seconds < 3600:
        return f"{round(seconds / 60)} min"
    if seconds < 86400:
        return f"{round(seconds / 3600)} h"
    days = round(seconds / 86400)
    if days < 31:
        return f"{days} d"
    if days < 365:
        return f"{round(days / 30)} mo"
    return f"{days / 365:.1f} y"
