"""Inactivity-bounded work session tracking."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
import json
from typing import Callable

from app.core.events import ActivityObservation, FileActivity
from app.core.time import utc_now
from app.database.models import WorkSession
from app.database.repositories import SessionRepository


class SessionMonitor:
    """Create and close sessions based on meaningful high-level activity."""

    def __init__(self, repository: SessionRepository, inactivity_timeout_seconds: int = 900) -> None:
        self.repository = repository
        self.inactivity_timeout = timedelta(seconds=max(30, inactivity_timeout_seconds))
        self._active: WorkSession | None = None
        self._last_activity: datetime | None = None
        self._applications: Counter[str] = Counter()
        self._recent_activity: list[str] = []
        self._on_closed: Callable[[WorkSession], None] | None = None

    def set_on_closed(self, callback: Callable[[WorkSession], None]) -> None:
        self._on_closed = callback

    @property
    def active_session(self) -> WorkSession | None:
        return self._active

    def record_observation(self, observation: ActivityObservation | FileActivity) -> WorkSession:
        timestamp = observation.timestamp
        if self._active is None:
            self._active = self.repository.create(timestamp)
        self._last_activity = timestamp
        if isinstance(observation, ActivityObservation):
            self._applications[observation.application_name] += 1
            activity_label = observation.application_name
        else:
            activity_label = f"Filesystem: {observation.event_type}"
        self._recent_activity.append(activity_label)
        self._recent_activity = self._recent_activity[-10:]
        self._persist_state(timestamp)
        return self._active

    def tick(self, now: datetime | None = None) -> WorkSession | None:
        if self._active is None or self._last_activity is None:
            return None
        current_time = now or utc_now()
        if current_time - self._last_activity >= self.inactivity_timeout:
            return self.close(current_time)
        return self._active

    def close(self, ended_at: datetime | None = None) -> WorkSession | None:
        if self._active is None:
            return None
        ended_at = ended_at or utc_now()
        primary = self._applications.most_common(1)[0][0] if self._applications else None
        updated = self.repository.update(
            self._active.id,
            ended_at=ended_at,
            primary_application=primary,
            summary=self._summary(primary),
            last_state=json.dumps({"recent_activity": self._recent_activity}),
        )
        if updated and self._on_closed:
            self._on_closed(updated)
        self._active = None
        self._last_activity = None
        self._applications.clear()
        self._recent_activity.clear()
        return updated

    def _persist_state(self, timestamp: datetime) -> None:
        if self._active is None:
            return
        primary = self._applications.most_common(1)[0][0] if self._applications else None
        self._active = self.repository.update(
            self._active.id,
            primary_application=primary,
            summary=self._summary(primary),
            last_state=json.dumps({"last_activity_at": timestamp.isoformat(), "recent_activity": self._recent_activity}),
        )

    def _summary(self, primary: str | None) -> str:
        if not primary:
            return "Activity recorded without an identified foreground application."
        return f"Worked primarily in {primary}; recent activity: {', '.join(self._recent_activity[-3:])}."
