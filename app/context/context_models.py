"""Context-specific value objects."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, frozen=True)
class ContextInput:
    """Inputs passed to deterministic context building."""

    timestamp: datetime
    application_name: str | None
    window_title: str | None
    recent_applications: tuple[str, ...]
    recent_activity: str | None
    open_tasks: tuple[tuple[int, str], ...]

