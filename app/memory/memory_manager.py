"""Facade over context and session memory."""

from __future__ import annotations

from app.context.context_engine import ContextEngine
from app.database.models import WorkSession
from app.memory.session_memory import SessionMemory, SessionMemoryStore


class MemoryManager:
    def __init__(self, context_engine: ContextEngine, session_memory: SessionMemoryStore) -> None:
        self.context_engine = context_engine
        self.session_memory = session_memory

    def latest_session(self) -> SessionMemory | None:
        return self.session_memory.latest()

    def save_session_context(self, session: WorkSession, project_context: str | None = None) -> WorkSession:
        """Attach the last known context to a closed session."""

        if project_context is not None:
            session.project_context = project_context
        return session

