"""Aggregate persisted observations into current context snapshots."""

from __future__ import annotations

from datetime import datetime
import json

from app.context.context_builder import ContextBuilder
from app.context.context_models import ContextInput
from app.core.events import CurrentContext
from app.core.time import utc_now
from app.database.repositories import ActivityRepository, ContextRepository, TaskRepository


class ContextEngine:
    """Produce deterministic current context and persist snapshots."""

    def __init__(self, activity_repository: ActivityRepository, context_repository: ContextRepository, task_repository: TaskRepository, builder: ContextBuilder | None = None) -> None:
        self.activity_repository = activity_repository
        self.context_repository = context_repository
        self.task_repository = task_repository
        self.builder = builder or ContextBuilder()
        self._current: CurrentContext | None = None

    @property
    def current(self) -> CurrentContext | None:
        return self._current

    def refresh(self, now: datetime | None = None, persist: bool = True) -> CurrentContext:
        events = self.activity_repository.recent(limit=25)
        latest = events[-1] if events else None
        open_tasks = tuple((task.id, task.title) for task in self.task_repository.list_open())
        recent_apps = tuple(event.application_name for event in events if event.application_name != "Filesystem")
        metadata: dict[str, object] = {}
        if latest and latest.metadata_json:
            try:
                metadata = json.loads(latest.metadata_json)
            except json.JSONDecodeError:
                metadata = {}
        recent_activity = latest.event_type if latest else None
        if metadata.get("path"):
            recent_activity = f"{latest.event_type}: {metadata['path']}"
        context = self.builder.build(
            ContextInput(
                timestamp=now or utc_now(),
                application_name=latest.application_name if latest else None,
                window_title=latest.window_title if latest else None,
                recent_applications=recent_apps,
                recent_activity=recent_activity,
                open_tasks=open_tasks,
            )
        )
        self._current = context
        if persist:
            self.context_repository.add(context)
        return context
