"""Small immutable contracts shared by monitors and higher-level services."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True, frozen=True)
class ActivityObservation:
    """A safe high-level observation; it never contains keystrokes or content."""

    timestamp: datetime
    application_name: str
    process_name: str
    window_title: str | None
    event_type: str = "foreground_changed"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class FileActivity:
    """A filesystem metadata event for a configured directory."""

    timestamp: datetime
    event_type: str
    path: str
    is_directory: bool = False


@dataclass(slots=True, frozen=True)
class CurrentContext:
    """The context shown to the user and stored as a snapshot."""

    timestamp: datetime
    active_application: str | None
    active_window: str | None
    project_context: str | None
    current_task_id: int | None
    last_activity: str | None
    summary: str

