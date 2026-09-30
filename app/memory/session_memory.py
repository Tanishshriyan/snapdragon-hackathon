"""Read and serialize the most recent saved session for resume UI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json

from app.database.models import WorkSession
from app.database.repositories import SessionRepository


@dataclass(slots=True, frozen=True)
class SessionMemory:
    session_id: int
    started_at: datetime
    ended_at: datetime | None
    primary_application: str | None
    project_context: str | None
    summary: str
    recent_activity: tuple[str, ...]

    @classmethod
    def from_model(cls, session: WorkSession) -> "SessionMemory":
        try:
            state = json.loads(session.last_state or "{}")
        except json.JSONDecodeError:
            state = {}
        return cls(
            session_id=session.id,
            started_at=session.started_at,
            ended_at=session.ended_at,
            primary_application=session.primary_application,
            project_context=session.project_context,
            summary=session.summary,
            recent_activity=tuple(state.get("recent_activity", ())),
        )


class SessionMemoryStore:
    def __init__(self, repository: SessionRepository) -> None:
        self.repository = repository

    def latest(self) -> SessionMemory | None:
        session = self.repository.latest()
        return SessionMemory.from_model(session) if session else None

