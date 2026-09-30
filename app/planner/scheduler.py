"""Small date-oriented planner helper kept separate for future scheduling rules."""

from datetime import date, timedelta


class Scheduler:
    """Provide date labels without creating OS-level scheduled jobs."""

    @staticmethod
    def tomorrow(today: date | None = None) -> date:
        return (today or date.today()) + timedelta(days=1)

