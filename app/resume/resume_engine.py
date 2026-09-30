"""Resume presentation and explicit, non-destructive workspace preparation."""

from __future__ import annotations

from dataclasses import dataclass

from app.memory.session_memory import SessionMemory, SessionMemoryStore


@dataclass(slots=True, frozen=True)
class ResumeContext:
    session: SessionMemory | None
    last_task_title: str | None = None


@dataclass(slots=True, frozen=True)
class WorkspacePreparation:
    prepared: bool
    message: str


class ResumeEngine:
    def __init__(self, session_memory: SessionMemoryStore) -> None:
        self.session_memory = session_memory

    def load_resume_context(self, last_task_title: str | None = None) -> ResumeContext:
        return ResumeContext(self.session_memory.latest(), last_task_title)

    def prepare_workspace(self, context: ResumeContext) -> WorkspacePreparation:
        if context.session is None:
            return WorkspacePreparation(False, "There is no saved session to prepare.")
        app = context.session.primary_application or "the last application"
        project = context.session.project_context or "the last project context"
        return WorkspacePreparation(
            True,
            f"Workspace plan ready for {app} ({project}). Automatic application launch is not enabled in Phase 1.",
        )

