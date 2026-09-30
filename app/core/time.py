"""UTC clock helpers with naive values for SQLite's existing DateTime columns."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return a timezone-correct UTC value without deprecated ``utcnow``."""

    return datetime.now(UTC).replace(tzinfo=None)

